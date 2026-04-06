"""database.db：create_tables / drop_tables（打桩引擎）。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.database.db import create_tables, drop_tables


@pytest.mark.asyncio
async def test_create_tables_runs_metadata_create_all() -> None:
    conn = MagicMock()
    conn.run_sync = AsyncMock()

    class _BeginCM:
        async def __aenter__(self):
            return conn

        async def __aexit__(self, *args):
            return None

    engine = MagicMock()
    engine.begin = MagicMock(return_value=_BeginCM())

    with patch("backend.database.db.async_engine", engine):
        await create_tables()

    conn.run_sync.assert_awaited_once()
    sync_fn = conn.run_sync.call_args[0][0]
    assert callable(sync_fn)


@pytest.mark.asyncio
async def test_drop_tables_runs_metadata_drop_all() -> None:
    conn = MagicMock()
    conn.run_sync = AsyncMock()

    class _BeginCM:
        async def __aenter__(self):
            return conn

        async def __aexit__(self, *args):
            return None

    engine = MagicMock()
    engine.begin = MagicMock(return_value=_BeginCM())

    with patch("backend.database.db.async_engine", engine):
        await drop_tables()

    conn.run_sync.assert_awaited_once()
