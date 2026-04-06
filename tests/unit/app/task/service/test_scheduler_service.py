"""TaskSchedulerService 单元测试。"""

import json

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.task.enums import TaskSchedulerType
from backend.app.task.schema.scheduler import CreateTaskSchedulerParam, UpdateTaskSchedulerParam
from backend.app.task.service.scheduler_service import TaskSchedulerService
from backend.common.exception import errors


@pytest.mark.asyncio
async def test_get_raises_not_found() -> None:
    with patch('backend.app.task.service.scheduler_service.task_scheduler_dao') as dao:
        dao.get = AsyncMock(return_value=None)
        db = AsyncMock()
        with pytest.raises(errors.NotFoundError) as ei:
            await TaskSchedulerService.get(db=db, pk=1)
        assert ei.value.msg == '任务调度不存在'


@pytest.mark.asyncio
async def test_get_all_delegates() -> None:
    seq = [MagicMock()]
    with patch('backend.app.task.service.scheduler_service.task_scheduler_dao') as dao:
        dao.get_all = AsyncMock(return_value=seq)
        db = AsyncMock()
        out = await TaskSchedulerService.get_all(db=db)
        assert out == seq


@pytest.mark.asyncio
async def test_create_raises_conflict() -> None:
    with patch('backend.app.task.service.scheduler_service.task_scheduler_dao') as dao:
        dao.get_by_name = AsyncMock(return_value=MagicMock())
        db = AsyncMock()
        obj = MagicMock(spec=CreateTaskSchedulerParam)
        obj.name = 'dup'
        obj.type = TaskSchedulerType.INTERVAL
        with pytest.raises(errors.ConflictError) as ei:
            await TaskSchedulerService.create(db=db, obj=obj)
        assert ei.value.msg == '任务调度已存在'


@pytest.mark.asyncio
async def test_create_interval_calls_dao() -> None:
    with patch('backend.app.task.service.scheduler_service.task_scheduler_dao') as dao:
        dao.get_by_name = AsyncMock(return_value=None)
        dao.create = AsyncMock()
        db = AsyncMock()
        obj = MagicMock(spec=CreateTaskSchedulerParam)
        obj.name = 'new'
        obj.type = TaskSchedulerType.INTERVAL
        await TaskSchedulerService.create(db=db, obj=obj)
        dao.create.assert_awaited_once_with(db, obj)


@pytest.mark.asyncio
async def test_create_crontab_validates_expression() -> None:
    with patch('backend.app.task.service.scheduler_service.task_scheduler_dao') as dao:
        dao.get_by_name = AsyncMock(return_value=None)
        db = AsyncMock()
        obj = MagicMock(spec=CreateTaskSchedulerParam)
        obj.name = 'c'
        obj.type = TaskSchedulerType.CRONTAB
        obj.crontab = 'bad'
        with patch(
            'backend.app.task.service.scheduler_service.crontab_verify',
            side_effect=errors.RequestError(msg='Crontab 表达式非法'),
        ):
            with pytest.raises(errors.RequestError):
                await TaskSchedulerService.create(db=db, obj=obj)


@pytest.mark.asyncio
async def test_update_raises_not_found() -> None:
    with patch('backend.app.task.service.scheduler_service.task_scheduler_dao') as dao:
        dao.get = AsyncMock(return_value=None)
        db = AsyncMock()
        obj = MagicMock(spec=UpdateTaskSchedulerParam)
        with pytest.raises(errors.NotFoundError):
            await TaskSchedulerService.update(db=db, pk=1, obj=obj)


@pytest.mark.asyncio
async def test_update_status_toggles() -> None:
    ts = MagicMock()
    ts.enabled = True
    with patch('backend.app.task.service.scheduler_service.task_scheduler_dao') as dao:
        dao.get = AsyncMock(return_value=ts)
        dao.set_status = AsyncMock(return_value=1)
        db = AsyncMock()
        n = await TaskSchedulerService.update_status(db=db, pk=3)
        assert n == 1
        dao.set_status.assert_awaited_once_with(db, 3, status=False)


@pytest.mark.asyncio
async def test_delete_raises_not_found() -> None:
    with patch('backend.app.task.service.scheduler_service.task_scheduler_dao') as dao:
        dao.get = AsyncMock(return_value=None)
        db = AsyncMock()
        with pytest.raises(errors.NotFoundError):
            await TaskSchedulerService.delete(db=db, pk=9)


@pytest.mark.asyncio
async def test_execute_no_workers() -> None:
    with patch('backend.app.task.service.scheduler_service.run_in_threadpool', new_callable=AsyncMock) as rip:
        rip.return_value = []
        db = AsyncMock()
        with pytest.raises(errors.ServerError) as ei:
            await TaskSchedulerService.execute(db=db, pk=1)
        assert 'Celery Worker' in (ei.value.msg or '')


@pytest.mark.asyncio
async def test_execute_send_task() -> None:
    ts = MagicMock()
    ts.task = 'backend.app.task.tasks.tasks.ping'
    ts.args = json.dumps([1])
    ts.kwargs = json.dumps({'a': 2})
    with patch('backend.app.task.service.scheduler_service.run_in_threadpool', new_callable=AsyncMock) as rip:
        rip.return_value = [{'ok': True}]
        with patch('backend.app.task.service.scheduler_service.task_scheduler_dao') as dao:
            dao.get = AsyncMock(return_value=ts)
            with patch('backend.app.task.service.scheduler_service.celery_app') as cap:
                cap.send_task = MagicMock()
                db = AsyncMock()
                await TaskSchedulerService.execute(db=db, pk=5)
                cap.send_task.assert_called_once_with(
                    name=ts.task,
                    args=[1],
                    kwargs={'a': 2},
                )


@pytest.mark.asyncio
async def test_execute_invalid_json_args() -> None:
    ts = MagicMock()
    ts.task = 't'
    ts.args = 'not-json'
    ts.kwargs = None
    with patch(
        'backend.app.task.service.scheduler_service.run_in_threadpool', new_callable=AsyncMock, return_value=[{}]
    ):
        with patch('backend.app.task.service.scheduler_service.task_scheduler_dao') as dao:
            dao.get = AsyncMock(return_value=ts)
            db = AsyncMock()
            with pytest.raises(errors.RequestError) as ei:
                await TaskSchedulerService.execute(db=db, pk=1)
            assert '参数非法' in (ei.value.msg or '')
