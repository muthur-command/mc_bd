"""CRUDTaskScheduler。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sqlalchemy import Select

from backend.app.task.crud.crud_scheduler import task_scheduler_dao
from backend.app.task.schema.scheduler import CreateTaskSchedulerParam, UpdateTaskSchedulerParam


@pytest.mark.asyncio
async def test_get_delegates_select_model() -> None:
    db = AsyncMock()
    row = object()
    with patch.object(task_scheduler_dao, 'select_model', new_callable=AsyncMock, return_value=row) as sm:
        out = await task_scheduler_dao.get(db, 4)
        assert out is row
        sm.assert_awaited_once_with(db, 4)


@pytest.mark.asyncio
async def test_get_select_returns_select() -> None:
    sel = await task_scheduler_dao.get_select('job', 1)
    assert isinstance(sel, Select)


@pytest.mark.asyncio
async def test_get_by_name_delegates() -> None:
    db = AsyncMock()
    with patch.object(task_scheduler_dao, 'select_model_by_column', new_callable=AsyncMock) as sm:
        await task_scheduler_dao.get_by_name(db, 'n')
        sm.assert_awaited_once_with(db, name='n')


@pytest.mark.asyncio
async def test_create_delegates_create_model() -> None:
    db = AsyncMock()
    obj = MagicMock(spec=CreateTaskSchedulerParam)
    with patch.object(task_scheduler_dao, 'create_model', new_callable=AsyncMock) as cm:
        await task_scheduler_dao.create(db, obj)
        cm.assert_awaited_once_with(db, obj, flush=True)


@pytest.mark.asyncio
async def test_update_mutates_instance() -> None:
    db = AsyncMock()
    inst = MagicMock()
    obj = MagicMock(spec=UpdateTaskSchedulerParam)
    obj.model_dump.return_value = {'name': 'x'}
    with patch.object(task_scheduler_dao, 'get', new_callable=AsyncMock, return_value=inst):
        n = await task_scheduler_dao.update(db, 1, obj)
        assert n == 1
        assert inst.name == 'x'


@pytest.mark.asyncio
async def test_delete_removes_row() -> None:
    db = AsyncMock()
    db.delete = AsyncMock()
    inst = MagicMock()
    with patch.object(task_scheduler_dao, 'get', new_callable=AsyncMock, return_value=inst):
        n = await task_scheduler_dao.delete(db, 7)
        assert n == 1
        db.delete.assert_awaited_once_with(inst)
