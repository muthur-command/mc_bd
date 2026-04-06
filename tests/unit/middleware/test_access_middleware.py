"""middleware.access_middleware：在 ContextMiddleware 下可跑通。"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager

from fastapi import FastAPI
from starlette.testclient import TestClient
from starlette_context.middleware import ContextMiddleware
from starlette_context.plugins import RequestIdPlugin

from backend.middleware.access_middleware import AccessMiddleware


def test_access_middleware_with_context_stack(
    fastapi_app_empty: FastAPI,
    starlette_client_context: Callable[..., AbstractContextManager[TestClient]],
) -> None:
    app = fastapi_app_empty
    app.add_middleware(AccessMiddleware)
    app.add_middleware(
        ContextMiddleware,
        plugins=[RequestIdPlugin(validate=False)],
    )

    @app.get("/ping")
    async def _ping() -> dict:
        return {"pong": True}

    with starlette_client_context(app) as client:
        r = client.get("/ping")
    assert r.status_code == 200
    assert r.json() == {"pong": True}
