"""database.db：异步引擎工厂、会话工厂、uuid4_str。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import URL

from backend.database.db import (
    create_database_async_engine,
    create_database_async_session,
    get_db,
    get_db_transaction,
    uuid4_str,
)


def test_create_database_async_engine_uses_pool_settings() -> None:
    url = URL.create("sqlite+aiosqlite", database=":memory:")
    fake_engine = MagicMock()
    with patch("backend.database.db.create_async_engine", return_value=fake_engine) as ce:
        out = create_database_async_engine(url)
    assert out is fake_engine
    kwargs = ce.call_args.kwargs
    assert kwargs["pool_size"] == 10
    assert kwargs["max_overflow"] == 20
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["future"] is True


def test_create_database_async_session_binds_engine() -> None:
    engine = MagicMock()
    sm = create_database_async_session(engine)
    assert sm.kw["bind"] is engine
    assert sm.kw["autoflush"] is False
    assert sm.kw["expire_on_commit"] is False


def test_uuid4_str_is_valid_uuid_format() -> None:
    s = uuid4_str()
    assert len(s) == 36
    assert s.count("-") == 4


@pytest.mark.asyncio
async def test_get_db_yields_session_from_context() -> None:
    mock_session = MagicMock()

    class _CM:
        async def __aenter__(self):
            return mock_session

        async def __aexit__(self, *args):
            return None

    factory = MagicMock(return_value=_CM())

    with patch("backend.database.db.async_db_session", factory):
        out = []
        async for s in get_db():
            out.append(s)
    assert out == [mock_session]
    factory.assert_called_once_with()


@pytest.mark.asyncio
async def test_get_db_transaction_uses_begin() -> None:
    mock_session = MagicMock()

    class _TxCM:
        async def __aenter__(self):
            return mock_session

        async def __aexit__(self, *args):
            return None

    maker = MagicMock()
    maker.begin = MagicMock(return_value=_TxCM())

    with patch("backend.database.db.async_db_session", maker):
        out = []
        async for s in get_db_transaction():
            out.append(s)
    assert out == [mock_session]
    maker.begin.assert_called_once_with()
