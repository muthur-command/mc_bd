"""backend.utils.locks — acquire_distributed_reload_lock。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_acquire_reload_lock_acquires_and_releases() -> None:
    lock = MagicMock()
    lock.acquire = AsyncMock()
    lock.owned = AsyncMock(return_value=True)
    lock.release = AsyncMock()

    path_mock = MagicMock()
    path_mock.touch = AsyncMock()
    path_mock.unlink = AsyncMock()

    with patch('backend.utils.locks.redis_client') as rc:
        rc.lock = MagicMock(return_value=lock)
        with patch('backend.utils.locks.anyio.Path', return_value=path_mock):
            from backend.utils.locks import acquire_distributed_reload_lock

            async with acquire_distributed_reload_lock():
                pass

    lock.acquire.assert_awaited_once()
    path_mock.touch.assert_awaited_once()
    path_mock.unlink.assert_awaited_once()
    lock.release.assert_awaited_once()
