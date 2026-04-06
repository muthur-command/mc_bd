"""CRUDLoginLog。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sqlalchemy import Select

from backend.app.admin.crud.crud_login_log import login_log_dao
from backend.app.admin.schema.login_log import CreateLoginLogParam


@pytest.mark.asyncio
async def test_get_select_returns_select() -> None:
    sel = await login_log_dao.get_select('user', 1, '127.0.0.1')
    assert isinstance(sel, Select)


@pytest.mark.asyncio
async def test_get_select_all_optional_none() -> None:
    sel = await login_log_dao.get_select(None, None, None)
    assert isinstance(sel, Select)


@pytest.mark.asyncio
async def test_create_delegates_create_model() -> None:
    db = AsyncMock()
    obj = MagicMock(spec=CreateLoginLogParam)
    with patch.object(login_log_dao, 'create_model', new_callable=AsyncMock) as cm:
        await login_log_dao.create(db, obj)
        cm.assert_awaited_once_with(db, obj, commit=True)


@pytest.mark.asyncio
async def test_delete_delegates() -> None:
    db = AsyncMock()
    with patch.object(login_log_dao, 'delete_model_by_column', new_callable=AsyncMock, return_value=3) as dm:
        n = await login_log_dao.delete(db, [10, 11, 12])
        assert n == 3
        dm.assert_awaited_once_with(db, allow_multiple=True, id__in=[10, 11, 12])


@pytest.mark.asyncio
async def test_delete_all_executes_delete() -> None:
    db = AsyncMock()
    db.execute = AsyncMock()
    await login_log_dao.delete_all(db)
    db.execute.assert_awaited_once()
