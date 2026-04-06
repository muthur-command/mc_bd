"""OAuth2 插件路由：社交绑定 API + 获取授权 URL（OAuth 回调依赖链过长，由服务层覆盖）。"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

from starlette.testclient import TestClient

from backend.core.conf import settings

_BASE = f"{settings.FASTAPI_API_V1_PATH}/oauth2"


def test_get_bindings(
    oauth2_api_client: TestClient,
    oauth2_auth_headers: dict[str, str],
) -> None:
    with patch(
        "backend.plugin.oauth2.api.v1.user_social.user_social_service.get_bindings",
        new_callable=AsyncMock,
        return_value=["Github"],
    ) as m:
        r = oauth2_api_client.get(f"{_BASE}/me/bindings", headers=oauth2_auth_headers)
    assert r.status_code == 200, r.text
    assert r.json().get("data") == ["Github"]
    m.assert_awaited_once()


def test_get_binding_auth_url_github(
    oauth2_api_client: TestClient,
    oauth2_auth_headers: dict[str, str],
) -> None:
    with patch(
        "backend.plugin.oauth2.api.v1.user_social.user_social_service.get_binding_auth_url",
        new_callable=AsyncMock,
        return_value="https://gh/oauth",
    ) as m:
        r = oauth2_api_client.get(
            f"{_BASE}/me/binding",
            headers=oauth2_auth_headers,
            params={"source": "Github"},
        )
    assert r.status_code == 200, r.text
    assert r.json().get("data") == "https://gh/oauth"
    m.assert_awaited_once()


def test_unbinding(
    oauth2_api_client: TestClient,
    oauth2_auth_headers: dict[str, str],
) -> None:
    with patch(
        "backend.plugin.oauth2.api.v1.user_social.user_social_service.unbinding",
        new_callable=AsyncMock,
    ) as m:
        r = oauth2_api_client.request(
            "DELETE",
            f"{_BASE}/me/unbinding",
            headers=oauth2_auth_headers,
            params={"source": "Google"},
        )
    assert r.status_code == 200, r.text
    m.assert_awaited_once()


def test_get_github_oauth2_login_url_stores_state_in_redis() -> None:
    from backend.plugin.oauth2.api.v1 import github as gh_mod

    with patch.object(gh_mod.uuid, "uuid4", return_value=MagicMock(hex="deadbeefcafe")):
        with patch(
            "backend.plugin.oauth2.api.v1.github.redis_client.setex",
            new_callable=AsyncMock,
        ) as setex:
            with patch(
                "backend.plugin.oauth2.api.v1.github.github_client.get_authorization_url",
                new_callable=AsyncMock,
                return_value="https://github.com/login?state=x",
            ) as auth:
                from fastapi import FastAPI
                from starlette.testclient import TestClient

                app = FastAPI()
                app.include_router(gh_mod.router, prefix="/gh")
                client = TestClient(app)
                r = client.get("/gh")
    assert r.status_code == 200
    assert r.json().get("data") == "https://github.com/login?state=x"
    setex.assert_awaited_once()
    key, ttl, raw = setex.await_args[0]
    assert key.startswith(settings.OAUTH2_STATE_REDIS_PREFIX)
    assert ttl == settings.OAUTH2_STATE_EXPIRE_SECONDS
    assert json.loads(raw).get("type") == "login"
    auth.assert_awaited_once()


def test_get_google_oauth2_login_url_stores_state_in_redis() -> None:
    from backend.plugin.oauth2.api.v1 import google as g_mod

    with patch.object(g_mod.uuid, "uuid4", return_value=MagicMock(hex="aaaabbbbcccc")):
        with patch(
            "backend.plugin.oauth2.api.v1.google.redis_client.setex",
            new_callable=AsyncMock,
        ) as setex:
            with patch(
                "backend.plugin.oauth2.api.v1.google.google_client.get_authorization_url",
                new_callable=AsyncMock,
                return_value="https://google/oauth?state=y",
            ):
                from fastapi import FastAPI
                from starlette.testclient import TestClient

                app = FastAPI()
                app.include_router(g_mod.router, prefix="/g")
                client = TestClient(app)
                r = client.get("/g")
    assert r.status_code == 200
    assert "google" in r.json().get("data", "")
    setex.assert_awaited_once()
    _key, _ttl, raw = setex.await_args[0]
    assert json.loads(raw).get("type") == "login"
