"""CRUDRole：委托 CRUDPlus 与 get_select 过滤。"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import Select

from backend.app.admin.crud.crud_role import role_dao
from backend.app.admin.schema.role import CreateRoleParam, UpdateRoleParam
from backend.common.enums import StatusType


@pytest.mark.asyncio
async def test_get_delegates_to_select_model() -> None:
    db = AsyncMock()
    role = object()
    with patch.object(role_dao, "select_model", new_callable=AsyncMock, return_value=role) as sm:
        out = await role_dao.get(db, 3)
        assert out is role
        sm.assert_awaited_once_with(db, 3)


@pytest.mark.asyncio
async def test_get_by_name_delegates() -> None:
    db = AsyncMock()
    with patch.object(role_dao, "select_model_by_column", new_callable=AsyncMock) as sm:
        await role_dao.get_by_name(db, "admin")
        sm.assert_awaited_once_with(db, name="admin")


@pytest.mark.asyncio
async def test_get_select_builds_select() -> None:
    sel = await role_dao.get_select("adm", StatusType.enable)
    assert isinstance(sel, Select)


@pytest.mark.asyncio
async def test_get_select_without_filters() -> None:
    sel = await role_dao.get_select(None, None)
    assert isinstance(sel, Select)


@pytest.mark.asyncio
async def test_create_update_delete_delegate() -> None:
    db = AsyncMock()
    create_obj = CreateRoleParam(name="r", status=StatusType.enable, remark=None)
    update_obj = UpdateRoleParam(name="r2", status=StatusType.disable, remark=None)
    with patch.object(role_dao, "create_model", new_callable=AsyncMock) as cm:
        await role_dao.create(db, create_obj)
        cm.assert_awaited_once_with(db, create_obj)
    with patch.object(role_dao, "update_model", new_callable=AsyncMock, return_value=1) as um:
        n = await role_dao.update(db, 5, update_obj)
        assert n == 1
        um.assert_awaited_once_with(db, 5, update_obj)
    with patch.object(role_dao, "delete_model_by_column", new_callable=AsyncMock, return_value=2) as dm:
        n = await role_dao.delete(db, [1, 2])
        assert n == 2
        dm.assert_awaited_once_with(db, allow_multiple=True, id__in=[1, 2])
