"""OAuth2Service：login / login_or_binding 分支（DAO、JWT、Redis、ctx 打桩）。"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.common.exception import errors
from backend.plugin.oauth2.enums import UserSocialAuthType, UserSocialType
from backend.plugin.oauth2.service.oauth2_service import OAuth2Service, oauth2_service


@pytest.mark.asyncio
async def test_login_or_binding_raises_without_state() -> None:
    with pytest.raises(errors.ForbiddenError):
        await oauth2_service.login_or_binding(
            db=AsyncMock(),
            response=MagicMock(),
            background_tasks=MagicMock(),
            user={"id": "1", "login": "a"},
            social=UserSocialType.github,
            state=None,
        )


@pytest.mark.asyncio
async def test_login_or_binding_raises_when_state_missing_in_redis() -> None:
    with patch(
        "backend.plugin.oauth2.service.oauth2_service.redis_client.get",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(errors.ForbiddenError):
            await oauth2_service.login_or_binding(
                db=AsyncMock(),
                response=MagicMock(),
                background_tasks=MagicMock(),
                user={"id": "1", "login": "a"},
                social=UserSocialType.github,
                state="st",
            )


@pytest.mark.asyncio
async def test_login_or_binding_binding_flow_calls_service_and_returns_none() -> None:
    payload = json.dumps({"type": UserSocialAuthType.binding.value, "user_id": 99})
    with patch(
        "backend.plugin.oauth2.service.oauth2_service.redis_client.get",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        with patch(
            "backend.plugin.oauth2.service.oauth2_service.redis_client.delete",
            new_callable=AsyncMock,
        ) as rdel:
            with patch(
                "backend.plugin.oauth2.service.oauth2_service.user_social_service.binding_with_oauth2",
                new_callable=AsyncMock,
            ) as bind:
                out = await oauth2_service.login_or_binding(
                    db=AsyncMock(),
                    response=MagicMock(),
                    background_tasks=MagicMock(),
                    user={"id": 12345, "login": "ghuser", "name": "N"},
                    social=UserSocialType.github,
                    state="s1",
                )
    assert out is None
    rdel.assert_awaited_once()
    bind.assert_awaited_once()
    call_kw = bind.await_args.kwargs
    assert call_kw["user_id"] == 99
    assert call_kw["sid"] == "12345"
    assert call_kw["source"] == UserSocialType.github


@pytest.mark.asyncio
async def test_login_or_binding_binding_raises_without_user_id_in_state() -> None:
    payload = json.dumps({"type": UserSocialAuthType.binding.value})
    with patch(
        "backend.plugin.oauth2.service.oauth2_service.redis_client.get",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        with patch(
            "backend.plugin.oauth2.service.oauth2_service.redis_client.delete",
            new_callable=AsyncMock,
        ):
            with pytest.raises(errors.ForbiddenError):
                await oauth2_service.login_or_binding(
                    db=AsyncMock(),
                    response=MagicMock(),
                    background_tasks=MagicMock(),
                    user={"id": "1", "login": "a"},
                    social=UserSocialType.github,
                    state="s2",
                )


@pytest.mark.asyncio
async def test_login_or_binding_login_flow_delegates_to_login() -> None:
    payload = json.dumps({"type": UserSocialAuthType.login.value})
    fake_token = MagicMock()
    with patch(
        "backend.plugin.oauth2.service.oauth2_service.redis_client.get",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        with patch(
            "backend.plugin.oauth2.service.oauth2_service.redis_client.delete",
            new_callable=AsyncMock,
        ):
            with patch.object(
                oauth2_service,
                "login",
                new_callable=AsyncMock,
                return_value=fake_token,
            ) as login_fn:
                out = await oauth2_service.login_or_binding(
                    db=AsyncMock(),
                    response=MagicMock(),
                    background_tasks=MagicMock(),
                    user={"id": "99", "login": "u", "name": "U", "email": "e@x.com"},
                    social=UserSocialType.github,
                    state="s3",
                )
    assert out is fake_token
    login_fn.assert_awaited_once()
    kw = login_fn.await_args.kwargs
    assert kw["sid"] == "99"
    assert kw["source"] == UserSocialType.github
    assert kw["username"] == "u"


@pytest.mark.asyncio
async def test_login_or_binding_invalid_state_type_raises() -> None:
    payload = json.dumps({"type": "other"})
    with patch(
        "backend.plugin.oauth2.service.oauth2_service.redis_client.get",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        with patch(
            "backend.plugin.oauth2.service.oauth2_service.redis_client.delete",
            new_callable=AsyncMock,
        ):
            with pytest.raises(errors.ForbiddenError):
                await oauth2_service.login_or_binding(
                    db=AsyncMock(),
                    response=MagicMock(),
                    background_tasks=MagicMock(),
                    user={"id": "1", "login": "a"},
                    social=UserSocialType.github,
                    state="s4",
                )


@pytest.mark.asyncio
async def test_login_google_user_field_mapping() -> None:
    """login_or_binding 对 Google 用户信息字段的归一化。"""
    payload = json.dumps({"type": UserSocialAuthType.login.value})
    with patch(
        "backend.plugin.oauth2.service.oauth2_service.redis_client.get",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        with patch(
            "backend.plugin.oauth2.service.oauth2_service.redis_client.delete",
            new_callable=AsyncMock,
        ):
            with patch.object(oauth2_service, "login", new_callable=AsyncMock) as login_fn:
                await oauth2_service.login_or_binding(
                    db=AsyncMock(),
                    response=MagicMock(),
                    background_tasks=MagicMock(),
                    user={
                        "id": "g1",
                        "name": "googlelogin",
                        "given_name": "G",
                        "email": "g@x.com",
                        "picture": "https://pic/x.png",
                    },
                    social=UserSocialType.google,
                    state="sg",
                )
    kw = login_fn.await_args.kwargs
    assert kw["sid"] == "g1"
    assert kw["username"] == "googlelogin"
    assert kw["nickname"] == "G"
    assert kw["email"] == "g@x.com"
    assert kw["avatar"] == "https://pic/x.png"


@pytest.mark.asyncio
async def test_login_existing_social_user_issues_tokens() -> None:
    db = AsyncMock()
    us = MagicMock()
    us.user_id = 7
    sys_user = MagicMock()
    sys_user.id = 7
    sys_user.username = "exists"
    sys_user.uuid = "uuuu-uuuu"
    sys_user.is_multi_login = True
    sys_user.nickname = "Nick"
    sys_user.avatar = "https://old/a.png"
    sys_user.email = None
    sys_user.phone = None

    at = MagicMock()
    at.access_token = "access"
    at.access_token_expire_time = datetime(2026, 1, 1)
    at.session_uuid = "sess-1"
    rt = MagicMock()
    rt.refresh_token = "refresh"
    rt.refresh_token_expire_time = datetime(2026, 6, 1)

    mock_ctx = MagicMock()
    mock_ctx.ip = "10.0.0.1"
    mock_ctx.os = "Linux"
    mock_ctx.browser = "Firefox"
    mock_ctx.device = "desktop"

    response = MagicMock()
    bg = MagicMock()

    with patch(
        "backend.plugin.oauth2.service.oauth2_service.user_social_dao.get_by_sid",
        new_callable=AsyncMock,
        return_value=us,
    ):
        with patch(
            "backend.plugin.oauth2.service.oauth2_service.user_dao.get",
            new_callable=AsyncMock,
            return_value=sys_user,
        ):
            with patch(
                "backend.plugin.oauth2.service.oauth2_service.jwt.create_access_token",
                new_callable=AsyncMock,
                return_value=at,
            ) as ca:
                with patch(
                    "backend.plugin.oauth2.service.oauth2_service.jwt.create_refresh_token",
                    new_callable=AsyncMock,
                    return_value=rt,
                ) as cr:
                    with patch(
                        "backend.plugin.oauth2.service.oauth2_service.user_dao.update_login_time",
                        new_callable=AsyncMock,
                    ):
                        with patch(
                            "backend.plugin.oauth2.service.oauth2_service.redis_client.delete",
                            new_callable=AsyncMock,
                        ):
                            with patch(
                                "backend.plugin.oauth2.service.oauth2_service.ctx",
                                mock_ctx,
                            ):
                                with patch(
                                    "backend.plugin.oauth2.service.oauth2_service.login_log_service.create",
                                ):
                                    out = await OAuth2Service.login(
                                        db=db,
                                        response=response,
                                        background_tasks=bg,
                                        sid="sid-1",
                                        source=UserSocialType.github,
                                        username="ignored",
                                        nickname="ignored",
                                        email="e@x.com",
                                        avatar="https://new/b.png",
                                    )

    ca.assert_awaited_once()
    cr.assert_awaited_once()
    assert out.access_token == "access"
    assert out.session_uuid == "sess-1"
    response.set_cookie.assert_called_once()
    bg.add_task.assert_called_once()
