"""RoleService 单元测试（DAO / 缓存打桩）。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.admin.schema.role import CreateRoleParam, DeleteRoleParam, UpdateRoleParam
from backend.app.admin.service.role_service import RoleService
from backend.common.enums import StatusType
from backend.common.exception import errors


@pytest.mark.asyncio
async def test_get_raises_not_found_when_missing() -> None:
    with patch("backend.app.admin.service.role_service.role_dao") as dao:
        dao.get = AsyncMock(return_value=None)
        db = AsyncMock()
        with pytest.raises(errors.NotFoundError) as ei:
            await RoleService.get(db=db, pk=1)
        assert ei.value.msg == "角色不存在"


@pytest.mark.asyncio
async def test_get_returns_role() -> None:
    role = MagicMock()
    with patch("backend.app.admin.service.role_service.role_dao") as dao:
        dao.get = AsyncMock(return_value=role)
        db = AsyncMock()
        out = await RoleService.get(db=db, pk=2)
        assert out is role


@pytest.mark.asyncio
async def test_create_raises_conflict_when_name_exists() -> None:
    with patch("backend.app.admin.service.role_service.role_dao") as dao:
        dao.get_by_name = AsyncMock(return_value=MagicMock())
        db = AsyncMock()
        obj = CreateRoleParam(name="r1", status=StatusType.enable, remark=None)
        with pytest.raises(errors.ConflictError) as ei:
            await RoleService.create(db=db, obj=obj)
        assert ei.value.msg == "角色已存在"


@pytest.mark.asyncio
async def test_create_calls_dao_when_name_free() -> None:
    with patch("backend.app.admin.service.role_service.role_dao") as dao:
        dao.get_by_name = AsyncMock(return_value=None)
        dao.create = AsyncMock()
        db = AsyncMock()
        obj = CreateRoleParam(name="new", status=StatusType.enable, remark="x")
        await RoleService.create(db=db, obj=obj)
        dao.create.assert_awaited_once_with(db, obj)


@pytest.mark.asyncio
async def test_update_raises_not_found() -> None:
    with patch("backend.app.admin.service.role_service.role_dao") as dao:
        dao.get = AsyncMock(return_value=None)
        db = AsyncMock()
        obj = UpdateRoleParam(name="x", status=StatusType.enable, remark=None)
        with pytest.raises(errors.NotFoundError) as ei:
            await RoleService.update(db=db, pk=9, obj=obj)
        assert ei.value.msg == "角色不存在"


@pytest.mark.asyncio
async def test_update_calls_cache_clear() -> None:
    role = MagicMock()
    role.name = "old"
    obj = UpdateRoleParam(name="old", status=StatusType.enable, remark=None)
    with patch("backend.app.admin.service.role_service.role_dao") as dao:
        dao.get = AsyncMock(return_value=role)
        dao.get_by_name = AsyncMock(return_value=None)
        dao.update = AsyncMock(return_value=1)
        with patch("backend.app.admin.service.role_service.user_cache_manager") as cache:
            cache.clear_by_role_id = AsyncMock()
            db = AsyncMock()
            n = await RoleService.update(db=db, pk=3, obj=obj)
            assert n == 1
            cache.clear_by_role_id.assert_awaited_once_with(db, [3])


@pytest.mark.asyncio
async def test_delete_calls_dao_and_cache() -> None:
    with patch("backend.app.admin.service.role_service.role_dao") as dao:
        dao.delete = AsyncMock(return_value=2)
        with patch("backend.app.admin.service.role_service.user_cache_manager") as cache:
            cache.clear_by_role_id = AsyncMock()
            db = AsyncMock()
            obj = DeleteRoleParam(pks=[1, 2])
            n = await RoleService.delete(db=db, obj=obj)
            assert n == 2
            dao.delete.assert_awaited_once_with(db, [1, 2])
            cache.clear_by_role_id.assert_awaited_once_with(db, [1, 2])
