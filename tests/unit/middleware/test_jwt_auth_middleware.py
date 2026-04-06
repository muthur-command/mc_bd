"""JwtAuthMiddleware：extract_token、authenticate 打桩。"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.common.exception.errors import TokenError
from backend.core.conf import settings
from backend.middleware.jwt_auth_middleware import AuthenticationError, JwtAuthMiddleware


def _request(path: str, authorization: str | None) -> MagicMock:
    req = MagicMock()
    req.url.path = path
    req.headers.get = MagicMock(side_effect=lambda k, d=None: authorization if k == "Authorization" else d)
    return req


def test_extract_token_no_header() -> None:
    assert JwtAuthMiddleware.extract_token(_request("/api/v1/x", None)) is None


def test_extract_token_bearer() -> None:
    t = JwtAuthMiddleware.extract_token(_request("/api/v1/x", "Bearer abc.def.ghi"))
    assert t == "abc.def.ghi"


def test_extract_token_non_bearer() -> None:
    assert JwtAuthMiddleware.extract_token(_request("/api/v1/x", "Basic x")) is None


def test_extract_token_login_path_excluded() -> None:
    path = f"{settings.FASTAPI_API_V1_PATH}/auth/login"
    assert JwtAuthMiddleware.extract_token(_request(path, "Bearer x")) is None


def test_auth_exception_handler_json_body() -> None:
    conn = MagicMock()
    resp = JwtAuthMiddleware.auth_exception_handler(
        conn,
        AuthenticationError(code=401, msg="unauthorized"),
    )
    assert resp.status_code == 401
    body = json.loads(resp.body.decode())
    assert body["code"] == 401
    assert body["msg"] == "unauthorized"
    assert body["data"] is None


@pytest.mark.asyncio
async def test_authenticate_no_token_returns_none() -> None:
    mw = JwtAuthMiddleware()
    with patch.object(JwtAuthMiddleware, "extract_token", return_value=None):
        out = await mw.authenticate(MagicMock())
        assert out is None


@pytest.mark.asyncio
async def test_authenticate_token_error_maps_to_authentication_error() -> None:
    mw = JwtAuthMiddleware()
    with patch.object(JwtAuthMiddleware, "extract_token", return_value="bad"):
        with patch(
            "backend.middleware.jwt_auth_middleware.jwt_authentication",
            new_callable=AsyncMock,
            side_effect=TokenError(),
        ):
            with pytest.raises(AuthenticationError):
                await mw.authenticate(MagicMock())


@pytest.mark.asyncio
async def test_authenticate_success_returns_credentials_and_user() -> None:
    mw = JwtAuthMiddleware()
    user = MagicMock()
    with patch.object(JwtAuthMiddleware, "extract_token", return_value="good"):
        with patch(
            "backend.middleware.jwt_auth_middleware.jwt_authentication",
            new_callable=AsyncMock,
            return_value=user,
        ):
            creds, u = await mw.authenticate(MagicMock())
            assert u is user
            assert "authenticated" in creds.scopes
