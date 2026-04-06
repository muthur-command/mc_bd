"""LoginLogService.get_list / delete 等（DAO + 分页打桩）。"""

from unittest.mock import AsyncMock, patch

import pytest

from backend.app.admin.schema.login_log import DeleteLoginLogParam
from backend.app.admin.service.login_log_service import LoginLogService


@pytest.mark.asyncio
async def test_get_list_uses_paging() -> None:
    with patch('backend.app.admin.service.login_log_service.login_log_dao') as dao:
        dao.get_select = AsyncMock(return_value='dummy-select')
        with patch('backend.app.admin.service.login_log_service.paging_data', new_callable=AsyncMock) as pg:
            pg.return_value = {'items': [], 'total': 0, 'page': 1, 'size': 20}
            db = AsyncMock()
            out = await LoginLogService.get_list(db=db, username='a', status=1, ip=None)
            assert out['total'] == 0
            dao.get_select.assert_awaited_once_with(username='a', status=1, ip=None)
            pg.assert_awaited_once_with(db, 'dummy-select')


@pytest.mark.asyncio
async def test_delete_delegates_to_dao() -> None:
    with patch('backend.app.admin.service.login_log_service.login_log_dao') as dao:
        dao.delete = AsyncMock(return_value=2)
        db = AsyncMock()
        obj = DeleteLoginLogParam(pks=[10, 11])
        n = await LoginLogService.delete(db=db, obj=obj)
        assert n == 2
        dao.delete.assert_awaited_once_with(db, [10, 11])


@pytest.mark.asyncio
async def test_delete_all_delegates_to_dao() -> None:
    with patch('backend.app.admin.service.login_log_service.login_log_dao') as dao:
        dao.delete_all = AsyncMock()
        db = AsyncMock()
        await LoginLogService.delete_all(db=db)
        dao.delete_all.assert_awaited_once_with(db)
