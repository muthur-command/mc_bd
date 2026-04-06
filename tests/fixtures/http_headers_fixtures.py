"""Authorization 等 HTTP 头默认值。"""

from __future__ import annotations

import pytest

from tests.helpers.http_headers import bearer_auth_headers


@pytest.fixture
def bearer_headers_default() -> dict[str, str]:
    """通用 Bearer 占位。"""
    return bearer_auth_headers('pytest-default-token')


@pytest.fixture
def bearer_headers_admin_api() -> dict[str, str]:
    """与 `tests/unit/app/admin/api/conftest` 中历史 token 一致，便于对照 OpenAPI 单测。"""
    return bearer_auth_headers('pytest-admin-api-token')


@pytest.fixture
def bearer_headers_task_api() -> dict[str, str]:
    """与 task API conftest 中历史 token 一致。"""
    return bearer_auth_headers('pytest-task-api-token')
