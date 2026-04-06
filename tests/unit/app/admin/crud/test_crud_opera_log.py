"""CRUDOperaLogDao。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import Select

from backend.app.admin.crud.crud_opera_log import opera_log_dao
from backend.app.admin.schema.opera_log import CreateOperaLogParam


@pytest.mark.asyncio
async def test_get_select_returns_select() -> None:
    sel = await opera_log_dao.get_select("op", 0, "10.0.0.1")
    assert isinstance(sel, Select)


@pytest.mark.asyncio
async def test_create_bulk_create_delete_delegate() -> None:
    db = AsyncMock()
    obj = MagicMock(spec=CreateOperaLogParam)
    with patch.object(opera_log_dao, "create_model", new_callable=AsyncMock) as cm:
        await opera_log_dao.create(db, obj)
        cm.assert_awaited_once_with(db, obj)
    with patch.object(opera_log_dao, "create_models", new_callable=AsyncMock) as cms:
        await opera_log_dao.bulk_create(db, [obj])
        cms.assert_awaited_once_with(db, [obj])
    with patch.object(opera_log_dao, "delete_model_by_column", new_callable=AsyncMock, return_value=1) as dm:
        n = await opera_log_dao.delete(db, [5])
        assert n == 1


@pytest.mark.asyncio
async def test_delete_all_executes_delete() -> None:
    db = AsyncMock()
    db.execute = AsyncMock()
    await opera_log_dao.delete_all(db)
    db.execute.assert_awaited_once()
