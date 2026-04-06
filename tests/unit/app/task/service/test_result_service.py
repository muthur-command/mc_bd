"""TaskResultService 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.task.schema.result import DeleteTaskResultParam
from backend.app.task.service.result_service import TaskResultService
from backend.common.exception import errors


@pytest.mark.asyncio
async def test_get_raises_not_found() -> None:
    with patch('backend.app.task.service.result_service.task_result_dao') as dao:
        dao.get = AsyncMock(return_value=None)
        db = AsyncMock()
        with pytest.raises(errors.NotFoundError) as ei:
            await TaskResultService.get(db=db, pk=1)
        assert ei.value.msg == '任务结果不存在'


@pytest.mark.asyncio
async def test_get_returns_row() -> None:
    row = MagicMock()
    with patch('backend.app.task.service.result_service.task_result_dao') as dao:
        dao.get = AsyncMock(return_value=row)
        db = AsyncMock()
        out = await TaskResultService.get(db=db, pk=2)
        assert out is row


@pytest.mark.asyncio
async def test_get_list_uses_paging() -> None:
    page = {'items': [], 'total': 0, 'page': 1, 'size': 20, 'total_pages': 0, 'links': {}}
    with patch('backend.app.task.service.result_service.task_result_dao') as dao:
        dao.get_select = AsyncMock(return_value='sel')
        with patch('backend.app.task.service.result_service.paging_data', new_callable=AsyncMock) as pg:
            pg.return_value = page
            db = AsyncMock()
            out = await TaskResultService.get_list(db=db, name='n', task_id='tid')
            assert out == page
            dao.get_select.assert_awaited_once_with('n', 'tid')
            pg.assert_awaited_once_with(db, 'sel')


@pytest.mark.asyncio
async def test_delete_delegates() -> None:
    with patch('backend.app.task.service.result_service.task_result_dao') as dao:
        dao.delete = AsyncMock(return_value=2)
        db = AsyncMock()
        obj = DeleteTaskResultParam(pks=[1, 2])
        n = await TaskResultService.delete(db=db, obj=obj)
        assert n == 2
        dao.delete.assert_awaited_once_with(db, [1, 2])
