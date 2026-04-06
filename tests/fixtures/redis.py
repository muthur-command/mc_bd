"""Redis 异步客户端桩（无真实连接）。"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def async_redis_mock() -> AsyncMock:
    """常用命令已为 `AsyncMock`，可按用例覆盖 `return_value` / `side_effect`。"""
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.set = AsyncMock(return_value=True)
    r.delete = AsyncMock(return_value=1)
    r.exists = AsyncMock(return_value=0)
    r.ping = AsyncMock(return_value=True)
    r.incr = AsyncMock(return_value=1)
    r.expire = AsyncMock(return_value=True)
    return r
