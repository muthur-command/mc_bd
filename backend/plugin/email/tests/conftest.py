"""Email 插件 API 单测：挂载 emails v1 + JWT + DB 依赖覆盖。"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from fastapi import FastAPI
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette_context.middleware import ContextMiddleware
from starlette_context.plugins import RequestIdPlugin

from backend.database.db import get_db, get_db_transaction
from backend.middleware.jwt_auth_middleware import JwtAuthMiddleware
from backend.plugin.email.api.router import v1 as email_v1
from tests.helpers.admin_test_user import default_admin_jwt_user
from tests.helpers.fastapi_testing import noop_rate_limiter_call, starlette_test_client

if TYPE_CHECKING:
    from collections.abc import Generator

    from starlette.testclient import TestClient


@pytest.fixture
def email_api_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        ContextMiddleware,
        plugins=[RequestIdPlugin(validate=False)],
    )
    app.add_middleware(
        AuthenticationMiddleware,
        backend=JwtAuthMiddleware(),
        on_error=JwtAuthMiddleware.auth_exception_handler,
    )
    app.include_router(email_v1)

    async def _mock_db() -> AsyncMock:
        yield AsyncMock()

    async def _mock_db_tx() -> AsyncMock:
        yield AsyncMock()

    app.dependency_overrides[get_db] = _mock_db
    app.dependency_overrides[get_db_transaction] = _mock_db_tx
    return app


@pytest.fixture
def email_api_client(email_api_app: FastAPI) -> Generator[TestClient, None, None]:
    with starlette_test_client(email_api_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def email_auth_headers(bearer_headers_admin_api: dict[str, str]) -> dict[str, str]:
    return bearer_headers_admin_api


@pytest.fixture(autouse=True)
def _email_noop_rate_limiter() -> Generator[None, None, None]:
    with noop_rate_limiter_call():
        yield


@pytest.fixture(autouse=True)
def _email_stub_jwt() -> Generator[None, None, None]:
    user = default_admin_jwt_user()
    with patch(
        'backend.middleware.jwt_auth_middleware.jwt_authentication',
        new_callable=AsyncMock,
        return_value=user,
    ):
        yield
