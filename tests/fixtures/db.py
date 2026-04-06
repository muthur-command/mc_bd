"""异步 DB 会话与 SQLAlchemy `execute`/`scalars` 结果桩。"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


@pytest.fixture
def async_mock_db() -> AsyncMock:
    """空白 `AsyncMock` 会话；按需挂 `execute` / `flush` 等。"""
    return AsyncMock()


@pytest.fixture
def async_mock_db_with_flush(async_mock_db: AsyncMock) -> AsyncMock:
    """含 `flush` / `refresh` 的异步会话（CRUD `add` 等常见路径）。"""
    async_mock_db.flush = AsyncMock()
    async_mock_db.refresh = AsyncMock()
    return async_mock_db


@pytest.fixture
def async_mock_db_with_delete(async_mock_db: AsyncMock) -> AsyncMock:
    """含 `delete` 的异步会话。"""
    async_mock_db.delete = AsyncMock()
    return async_mock_db


@pytest.fixture
def sqlalchemy_scalar_rows_factory() -> Callable[[Sequence[object]], MagicMock]:
    """`db.execute = AsyncMock(return_value=factory([row1, row2]))` 的快捷工厂。"""

    def _make(rows: Sequence[object]) -> MagicMock:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = list(rows)
        return mock_result

    return _make
