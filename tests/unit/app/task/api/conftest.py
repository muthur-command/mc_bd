"""Task API 单测：仅挂载 task v1 路由。"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from backend.app.task.api.router import v1 as task_v1
from tests.helpers.fastapi_testing import (
    build_app_with_pagination_and_mock_db,
    noop_rate_limiter_call,
    starlette_test_client,
)


def _register_task_v1(app: FastAPI) -> None:
    app.include_router(task_v1)


@pytest.fixture
def task_api_app() -> FastAPI:
    return build_app_with_pagination_and_mock_db(_register_task_v1)


@pytest.fixture
def task_client(task_api_app: FastAPI) -> Generator[TestClient, None, None]:
    with starlette_test_client(task_api_app) as c:
        yield c


@pytest.fixture
def task_auth_headers(bearer_headers_task_api: dict[str, str]) -> dict[str, str]:
    return bearer_headers_task_api


@pytest.fixture(autouse=True)
def _noop_rate_limiter_for_task_api() -> Generator[None, None, None]:
    with noop_rate_limiter_call():
        yield
