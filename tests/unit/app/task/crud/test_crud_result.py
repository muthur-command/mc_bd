"""CRUDTaskResult。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sqlalchemy import Select

from backend.app.task.crud.crud_result import task_result_dao


@pytest.mark.asyncio
async def test_get_delegates() -> None:
    db = AsyncMock()
    with patch.object(task_result_dao, 'select_model', new_callable=AsyncMock) as sm:
        sm.return_value = MagicMock()
        await task_result_dao.get(db, 1)
        sm.assert_awaited_once_with(db, 1)


@pytest.mark.asyncio
async def test_get_select_returns_select() -> None:
    sel = await task_result_dao.get_select('t', 'uuid-1')
    assert isinstance(sel, Select)


@pytest.mark.asyncio
async def test_delete_delegates() -> None:
    db = AsyncMock()
    with patch.object(task_result_dao, 'delete_model_by_column', new_callable=AsyncMock, return_value=3) as dm:
        n = await task_result_dao.delete(db, [1, 2, 3])
        assert n == 3
        dm.assert_awaited_once_with(db, allow_multiple=True, id__in=[1, 2, 3])
