"""FastAPI / Starlette 单测：分页、DB 依赖覆盖、限流桩、TestClient 上下文。"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from backend.database.db import get_db, get_db_transaction


def apply_mock_db_dependency_overrides(app: FastAPI) -> None:
    """将 `get_db` / `get_db_transaction` 替换为产出 `AsyncMock` 的依赖。"""

    async def _mock_db() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    async def _mock_db_tx() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    app.dependency_overrides[get_db] = _mock_db
    app.dependency_overrides[get_db_transaction] = _mock_db_tx


def build_app_with_pagination_and_mock_db(register: Callable[[FastAPI], None]) -> FastAPI:
    """`FastAPI` + `add_pagination` + 调用 `register(app)` 挂载路由 + mock DB 依赖。"""
    app = FastAPI()
    add_pagination(app)
    register(app)
    apply_mock_db_dependency_overrides(app)
    return app


@contextmanager
def noop_rate_limiter_call() -> Generator[None, None, None]:
    """FastAPILimiter 未初始化时，将 `RateLimiter.__call__` 变为空操作。"""

    async def _noop(_self: object, request: Request, response: Response) -> None:
        return None

    with patch("fastapi_limiter.depends.RateLimiter.__call__", _noop):
        yield


@contextmanager
def starlette_test_client(
    app: FastAPI,
    *,
    raise_server_exceptions: bool = True,
) -> Generator[TestClient, None, None]:
    """与 `with TestClient(...) as c` 等价，供 conftest fixture 使用。"""
    with TestClient(app, raise_server_exceptions=raise_server_exceptions) as client:
        yield client
