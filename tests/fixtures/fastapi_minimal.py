"""最小 FastAPI / Starlette 应用与 TestClient 上下文。"""

from __future__ import annotations

import pytest

from fastapi import FastAPI

from tests.helpers.fastapi_testing import starlette_test_client


@pytest.fixture
def fastapi_app_empty() -> FastAPI:
    """无路由；由用例自行 `@app.get` / `add_middleware`。"""
    return FastAPI()


@pytest.fixture
def starlette_client_context():
    """`tests.helpers.fastapi_testing.starlette_test_client` 别名。

    用法：`with starlette_client_context(app) as client:`。
    """
    return starlette_test_client
