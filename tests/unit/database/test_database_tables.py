"""database.db：create_tables / drop_tables（打桩引擎）。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.database.db import (
    CREATE_TABLES_LOCK_KEY,
    create_tables,
    drop_tables,
)


def _mock_engine_begin(conn: MagicMock) -> MagicMock:
    class _BeginCM:
        async def __aenter__(self):
            return conn

        async def __aexit__(self, *args):
            return None

    engine = MagicMock()
    engine.begin = MagicMock(return_value=_BeginCM())
    return engine


def _mock_redis_lock() -> tuple[MagicMock, MagicMock]:
    lock_cm = AsyncMock()
    lock_cm.__aenter__ = AsyncMock(return_value=True)
    lock_cm.__aexit__ = AsyncMock(return_value=None)

    redis_client = MagicMock()
    redis_client.lock = MagicMock(return_value=lock_cm)
    return redis_client, lock_cm


@pytest.mark.asyncio
async def test_create_tables_runs_metadata_create_all_under_redis_lock() -> None:
    conn = MagicMock()
    conn.run_sync = AsyncMock()
    engine = _mock_engine_begin(conn)
    redis_client, lock_cm = _mock_redis_lock()

    with (
        patch('backend.database.redis.redis_client', redis_client),
        patch('backend.database.db.async_engine', engine),
        patch(
            'backend.database.seed.seed_default_data_if_empty',
            new_callable=AsyncMock,
        ),
    ):
        await create_tables()

    redis_client.lock.assert_called_once_with(
        CREATE_TABLES_LOCK_KEY,
        timeout=300,
        blocking_timeout=120,
    )
    lock_cm.__aenter__.assert_awaited_once()
    lock_cm.__aexit__.assert_awaited_once()
    conn.run_sync.assert_awaited_once()
    sync_fn = conn.run_sync.call_args[0][0]
    assert callable(sync_fn)


@pytest.mark.asyncio
async def test_drop_tables_runs_metadata_drop_all() -> None:
    conn = MagicMock()
    conn.run_sync = AsyncMock()
    engine = _mock_engine_begin(conn)

    with patch('backend.database.db.async_engine', engine):
        await drop_tables()

    conn.run_sync.assert_awaited_once()
