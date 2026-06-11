"""database.seed：首次启动默认数据灌入。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.database.seed import (
    DEFAULT_DATA_SQL_FILENAME,
    execute_sql_file,
    get_default_data_sql_path,
    is_database_seeded,
    seed_default_data_if_empty,
)


def _mock_engine_connect(scalar=None) -> MagicMock:
    class _ConnectCM:
        async def __aenter__(self):
            return conn

        async def __aexit__(self, *args):
            return None

    class _BeginCM:
        async def __aenter__(self):
            return conn

        async def __aexit__(self, *args):
            return None

    conn = MagicMock()
    conn.execute = AsyncMock(return_value=MagicMock(scalar=MagicMock(return_value=scalar)))
    engine = MagicMock()
    engine.connect = MagicMock(return_value=_ConnectCM())
    engine.begin = MagicMock(return_value=_BeginCM())
    return engine


@pytest.mark.asyncio
async def test_is_database_seeded_true_when_user_exists() -> None:
    with patch('backend.database.seed.async_engine', _mock_engine_connect(scalar=1)):
        assert await is_database_seeded() is True


@pytest.mark.asyncio
async def test_is_database_seeded_false_when_empty() -> None:
    with patch('backend.database.seed.async_engine', _mock_engine_connect(scalar=None)):
        assert await is_database_seeded() is False


@pytest.mark.asyncio
async def test_seed_default_data_if_empty_skips_when_seeded() -> None:
    with (
        patch('backend.database.seed.is_database_seeded', new_callable=AsyncMock, return_value=True),
        patch('backend.database.seed.execute_sql_file', new_callable=AsyncMock) as execute,
    ):
        await seed_default_data_if_empty()
    execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_seed_default_data_if_empty_runs_sql_when_empty(tmp_path) -> None:
    sql_file = tmp_path / DEFAULT_DATA_SQL_FILENAME
    sql_file.write_text('INSERT INTO sys_user VALUES (1);', encoding='utf-8')

    with (
        patch('backend.database.seed.get_default_data_sql_path', return_value=sql_file),
        patch('backend.database.seed.is_database_seeded', new_callable=AsyncMock, return_value=False),
        patch('backend.database.seed.execute_sql_file', new_callable=AsyncMock) as execute,
    ):
        await seed_default_data_if_empty()

    execute.assert_awaited_once_with(sql_file)


@pytest.mark.asyncio
async def test_seed_default_data_if_empty_skips_missing_file(tmp_path) -> None:
    missing = tmp_path / 'missing.sql'
    with (
        patch('backend.database.seed.get_default_data_sql_path', return_value=missing),
        patch('backend.database.seed.is_database_seeded', new_callable=AsyncMock) as seeded,
        patch('backend.database.seed.execute_sql_file', new_callable=AsyncMock) as execute,
    ):
        await seed_default_data_if_empty()
    seeded.assert_not_awaited()
    execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_sql_file_runs_parsed_statements(tmp_path) -> None:
    sql_file = tmp_path / 'seed.sql'
    sql_file.write_text('SELECT 1;', encoding='utf-8')
    conn = MagicMock()
    conn.execute = AsyncMock()

    class _BeginCM:
        async def __aenter__(self):
            return conn

        async def __aexit__(self, *args):
            return None

    engine = MagicMock()
    engine.begin = MagicMock(return_value=_BeginCM())

    with (
        patch('backend.database.seed.async_engine', engine),
        patch(
            'backend.database.seed.parse_sql_script',
            new_callable=AsyncMock,
            return_value=['SELECT 1'],
        ),
    ):
        await execute_sql_file(sql_file)

    conn.execute.assert_awaited_once()


def test_get_default_data_sql_path_postgresql() -> None:
    from backend.common.enums import DataBaseType

    with patch('backend.database.seed.settings.DATABASE_TYPE', DataBaseType.postgresql):
        path = get_default_data_sql_path()
    assert path.name == DEFAULT_DATA_SQL_FILENAME
    assert path.parts[-2] == 'postgresql'


@pytest.mark.asyncio
async def test_create_tables_calls_seed_under_same_lock() -> None:
    from backend.database.db import CREATE_TABLES_LOCK_KEY, create_tables

    conn = MagicMock()
    conn.run_sync = AsyncMock()
    engine = MagicMock()

    class _BeginCM:
        async def __aenter__(self):
            return conn

        async def __aexit__(self, *args):
            return None

    engine.begin = MagicMock(return_value=_BeginCM())

    lock_cm = AsyncMock()
    lock_cm.__aenter__ = AsyncMock(return_value=True)
    lock_cm.__aexit__ = AsyncMock(return_value=None)
    redis_client = MagicMock()
    redis_client.lock = MagicMock(return_value=lock_cm)

    with (
        patch('backend.database.redis.redis_client', redis_client),
        patch('backend.database.db.async_engine', engine),
        patch('backend.database.seed.seed_default_data_if_empty', new_callable=AsyncMock) as seed,
    ):
        await create_tables()

    seed.assert_awaited_once()
    redis_client.lock.assert_called_once_with(
        CREATE_TABLES_LOCK_KEY,
        timeout=300,
        blocking_timeout=120,
    )
