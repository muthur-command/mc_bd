"""Admin API 单测：轻量 FastAPI + 分页 + DB 依赖覆盖 + JWT 认证中间件。"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette_context.middleware import ContextMiddleware
from starlette_context.plugins import RequestIdPlugin

from backend.app.admin.api.router import v1 as admin_v1
from backend.database.db import get_db, get_db_transaction
from backend.middleware.jwt_auth_middleware import JwtAuthMiddleware
from tests.helpers.admin_test_user import default_admin_jwt_user
from tests.helpers.fastapi_testing import (
    noop_rate_limiter_call,
    starlette_test_client,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from starlette.testclient import TestClient


def _register_admin_v1(app: FastAPI) -> None:
    app.include_router(admin_v1)


@pytest.fixture
def admin_api_app() -> FastAPI:
    app = FastAPI()
    add_pagination(app)
    app.add_middleware(
        ContextMiddleware,
        plugins=[RequestIdPlugin(validate=False)],
    )
    app.add_middleware(
        AuthenticationMiddleware,
        backend=JwtAuthMiddleware(),
        on_error=JwtAuthMiddleware.auth_exception_handler,
    )
    _register_admin_v1(app)

    async def _mock_db():
        yield AsyncMock()

    async def _mock_db_tx():
        yield AsyncMock()

    app.dependency_overrides[get_db] = _mock_db
    app.dependency_overrides[get_db_transaction] = _mock_db_tx
    return app


@pytest.fixture
def admin_client(admin_api_app: FastAPI) -> Generator[TestClient, None, None]:
    with starlette_test_client(admin_api_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def auth_headers(bearer_headers_admin_api: dict[str, str]) -> dict[str, str]:
    return bearer_headers_admin_api


@pytest.fixture(autouse=True)
def _noop_rate_limiter() -> Generator[None, None, None]:
    with noop_rate_limiter_call():
        yield


@pytest.fixture(autouse=True)
def _stub_jwt_authentication_for_admin_api() -> Generator[None, None, None]:
    """无真实 Redis 时仍能通过 `JwtAuthMiddleware` 注入 `request.user`。"""
    user = default_admin_jwt_user()
    with patch(
        'backend.middleware.jwt_auth_middleware.jwt_authentication',
        new_callable=AsyncMock,
        return_value=user,
    ):
        yield
