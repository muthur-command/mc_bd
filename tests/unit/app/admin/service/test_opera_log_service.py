"""OperaLogService 单元测试。"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.admin.schema.opera_log import CreateOperaLogParam, DeleteOperaLogParam
from backend.app.admin.service.opera_log_service import OperaLogService
from backend.common.enums import StatusType


def _sample_create_param() -> CreateOperaLogParam:
    return CreateOperaLogParam(
        trace_id="t1",
        username="admin",
        method="GET",
        title="测试",
        path="/api",
        ip="127.0.0.1",
        country=None,
        region=None,
        city=None,
        user_agent=None,
        os=None,
        browser=None,
        device=None,
        args=None,
        status=StatusType.enable,
        code="200",
        msg=None,
        cost_time=0.01,
        opera_time=datetime.now(),
    )


@pytest.mark.asyncio
async def test_create_delegates_to_dao() -> None:
    obj = _sample_create_param()
    with patch("backend.app.admin.service.opera_log_service.opera_log_dao") as dao:
        dao.create = AsyncMock()
        db = AsyncMock()
        await OperaLogService.create(db=db, obj=obj)
        dao.create.assert_awaited_once_with(db, obj)


@pytest.mark.asyncio
async def test_bulk_create_delegates_to_dao() -> None:
    objs = [_sample_create_param()]
    with patch("backend.app.admin.service.opera_log_service.opera_log_dao") as dao:
        dao.bulk_create = AsyncMock()
        db = AsyncMock()
        await OperaLogService.bulk_create(db=db, objs=objs)
        dao.bulk_create.assert_awaited_once_with(db, objs)


@pytest.mark.asyncio
async def test_delete_delegates_to_dao() -> None:
    with patch("backend.app.admin.service.opera_log_service.opera_log_dao") as dao:
        dao.delete = AsyncMock(return_value=3)
        db = AsyncMock()
        obj = DeleteOperaLogParam(pks=[1, 2, 3])
        n = await OperaLogService.delete(db=db, obj=obj)
        assert n == 3
        dao.delete.assert_awaited_once_with(db, [1, 2, 3])


@pytest.mark.asyncio
async def test_delete_all_delegates_to_dao() -> None:
    with patch("backend.app.admin.service.opera_log_service.opera_log_dao") as dao:
        dao.delete_all = AsyncMock()
        db = AsyncMock()
        await OperaLogService.delete_all(db=db)
        dao.delete_all.assert_awaited_once_with(db)
