"""Admin 域常见 `MagicMock` 实体与工厂（用户、角色等）。"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

_DEFAULT_USER_KW = {
    'id': 1,
    'username': 'pytest_user',
    'password': 'hashed_secret',
    'status': 1,
    'roles': [],
    'nickname': None,
    'avatar': None,
    'email': None,
    'phone': None,
}

_DEFAULT_ROLE_KW = {
    'id': 1,
    'name': 'pytest_role',
    'code': 'pytest',
}


@pytest.fixture
def make_mock_admin_user() -> Callable[..., MagicMock]:
    """合并默认字段与 `**overrides` 构造用户行桩（`roles` 可传入 `[MagicMock(), ...]`）。"""

    def _make(**overrides: object) -> MagicMock:
        u = MagicMock()
        for k, v in {**_DEFAULT_USER_KW, **overrides}.items():
            setattr(u, k, v)
        return u

    return _make


@pytest.fixture
def make_mock_admin_role() -> Callable[..., MagicMock]:
    """角色行桩工厂。"""

    def _make(**overrides: object) -> MagicMock:
        r = MagicMock()
        for k, v in {**_DEFAULT_ROLE_KW, **overrides}.items():
            setattr(r, k, v)
        return r

    return _make


@pytest.fixture
def mock_admin_user(make_mock_admin_user: Callable[..., MagicMock]) -> MagicMock:
    """单份默认用户桩（函数级隔离）。"""
    return make_mock_admin_user()
