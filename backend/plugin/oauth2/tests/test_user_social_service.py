"""UserSocialService：DAO / Redis / OAuth 客户端均 mock。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.common.exception import errors
from backend.plugin.oauth2.enums import UserSocialType
from backend.plugin.oauth2.service.user_social_service import UserSocialService


@pytest.mark.asyncio
async def test_get_bindings_returns_sources() -> None:
    b1 = MagicMock()
    b1.source = "Github"
    b2 = MagicMock()
    b2.source = "Google"
    with patch(
        "backend.plugin.oauth2.service.user_social_service.user_social_dao.get_by_user_id",
        new_callable=AsyncMock,
        return_value=[b1, b2],
    ):
        out = await UserSocialService.get_bindings(db=AsyncMock(), user_id=1)
    assert out == ["Github", "Google"]


@pytest.mark.asyncio
async def test_binding_with_oauth2_creates_when_valid() -> None:
    db = AsyncMock()
    with patch(
        "backend.plugin.oauth2.service.user_social_service.user_social_dao.check_binding",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with patch(
            "backend.plugin.oauth2.service.user_social_service.user_social_dao.get_by_sid",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "backend.plugin.oauth2.service.user_social_service.user_social_dao.create",
                new_callable=AsyncMock,
            ) as create:
                await UserSocialService.binding_with_oauth2(
                    db=db,
                    user_id=10,
                    sid="gh-99",
                    source=UserSocialType.github,
                )
    create.assert_awaited_once()


@pytest.mark.asyncio
async def test_binding_with_oauth2_raises_when_user_already_bound() -> None:
    with patch(
        "backend.plugin.oauth2.service.user_social_service.user_social_dao.check_binding",
        new_callable=AsyncMock,
        return_value=MagicMock(),
    ):
        with pytest.raises(errors.RequestError):
            await UserSocialService.binding_with_oauth2(
                db=AsyncMock(),
                user_id=1,
                sid="x",
                source=UserSocialType.google,
            )


@pytest.mark.asyncio
async def test_binding_with_oauth2_raises_when_sid_taken() -> None:
    with patch(
        "backend.plugin.oauth2.service.user_social_service.user_social_dao.check_binding",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with patch(
            "backend.plugin.oauth2.service.user_social_service.user_social_dao.get_by_sid",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ):
            with pytest.raises(errors.RequestError):
                await UserSocialService.binding_with_oauth2(
                    db=AsyncMock(),
                    user_id=1,
                    sid="taken",
                    source=UserSocialType.github,
                )


@pytest.mark.asyncio
async def test_unbinding_raises_when_not_bound() -> None:
    with patch(
        "backend.plugin.oauth2.service.user_social_service.user_social_dao.check_binding",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(errors.NotFoundError):
            await UserSocialService.unbinding(
                db=AsyncMock(),
                user_id=1,
                source=UserSocialType.github,
            )


@pytest.mark.asyncio
async def test_unbinding_delete_await_args_db_user_source() -> None:
    db = AsyncMock()
    bind = MagicMock()
    with patch(
        "backend.plugin.oauth2.service.user_social_service.user_social_dao.check_binding",
        new_callable=AsyncMock,
        return_value=bind,
    ):
        with patch(
            "backend.plugin.oauth2.service.user_social_service.user_social_dao.delete",
            new_callable=AsyncMock,
            return_value=3,
        ) as delete:
            n = await UserSocialService.unbinding(db=db, user_id=5, source=UserSocialType.github)
    assert n == 3
    delete.assert_awaited_once_with(db, 5, UserSocialType.github.value)


@pytest.mark.asyncio
async def test_get_binding_auth_url_github_writes_redis_and_returns_url() -> None:
    with patch(
        "backend.plugin.oauth2.service.user_social_service.redis_client.setex",
        new_callable=AsyncMock,
    ) as setex:
        with patch(
            "backend.plugin.oauth2.api.v1.github.github_client.get_authorization_url",
            new_callable=AsyncMock,
            return_value="https://github.com/login/oauth/authorize?x=1",
        ) as auth_url:
            url = await UserSocialService.get_binding_auth_url(user_id=7, source=UserSocialType.github)
    assert url == "https://github.com/login/oauth/authorize?x=1"
    setex.assert_awaited_once()
    auth_url.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_binding_auth_url_google_writes_redis_and_returns_url() -> None:
    with patch(
        "backend.plugin.oauth2.service.user_social_service.redis_client.setex",
        new_callable=AsyncMock,
    ):
        with patch(
            "backend.plugin.oauth2.api.v1.google.google_client.get_authorization_url",
            new_callable=AsyncMock,
            return_value="https://accounts.google.com/o/oauth2/v2/auth?q=1",
        ) as auth_url:
            url = await UserSocialService.get_binding_auth_url(user_id=8, source=UserSocialType.google)
    assert "google.com" in url
    auth_url.assert_awaited_once()
