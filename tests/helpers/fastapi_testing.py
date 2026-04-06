"""FastAPI / Starlette 单测：分页、DB 依赖覆盖、限流桩、TestClient 上下文。"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from backend.database.db import get_db, get_db_transaction

_rate_limiter_patch: object | None = None


def ensure_rate_limiter_patched_for_tests() -> None:
    """在注册带 ``Depends(RateLimiter(...))`` 的路由**之前**调用（幂等）。

    若在路由已 import 之后才 patch ``RateLimiter.__call__``，FastAPI 可能已把
    ``request``/``response`` 解析成 query，请求返回 422。
    """
    global _rate_limiter_patch
    if _rate_limiter_patch is not None:
        return

    async def _noop(self: object, request: Request, response: Response) -> None:
        return None

    _rate_limiter_patch = patch('fastapi_limiter.depends.RateLimiter.__call__', _noop)
    _rate_limiter_patch.start()


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Generator


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
    """兼容旧用法：与 ``ensure_rate_limiter_patched_for_tests()`` 等价（幂等）。"""
    ensure_rate_limiter_patched_for_tests()
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
