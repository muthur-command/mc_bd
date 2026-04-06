"""通用 unittest.mock 工厂，减少各测试文件中重复的 `AsyncMock()` 样板。"""

from __future__ import annotations

from unittest.mock import AsyncMock


def async_db_mock() -> AsyncMock:
    """异步 DB 会话占位（无默认行为；按需 `db.execute = AsyncMock()` 等）。"""
    return AsyncMock()
