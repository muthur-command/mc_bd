"""UserService 单元测试。"""

from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.admin.schema.user import AddUserParam
from backend.app.admin.service.user_service import UserService
from backend.common.exception import errors


@pytest.mark.asyncio
async def test_get_userinfo_raises_not_found(async_mock_db: AsyncMock) -> None:
    with patch('backend.app.admin.service.user_service.user_dao') as dao:
        dao.get_join = AsyncMock(return_value=None)
        with pytest.raises(errors.NotFoundError) as ei:
            await UserService.get_userinfo(db=async_mock_db, pk=1)
        assert ei.value.msg == 'error.user_not_found'


@pytest.mark.asyncio
async def test_get_roles_returns_user_roles(
    async_mock_db: AsyncMock,
    make_mock_admin_user: Callable[..., MagicMock],
) -> None:
    roles = [MagicMock()]
    user = make_mock_admin_user(roles=roles)
    with patch('backend.app.admin.service.user_service.user_dao') as dao:
        dao.get_join = AsyncMock(return_value=user)
        out = await UserService.get_roles(db=async_mock_db, pk=1)
        assert out == roles


@pytest.mark.asyncio
async def test_create_raises_when_username_exists(async_mock_db: AsyncMock) -> None:
    with patch('backend.app.admin.service.user_service.user_dao') as dao:
        dao.get_by_username = AsyncMock(return_value=MagicMock())
        obj = AddUserParam(username='u', password='p', roles=[1])
        with pytest.raises(errors.ConflictError) as ei:
            await UserService.create(db=async_mock_db, obj=obj)
        assert ei.value.msg == 'error.username_exists'


@pytest.mark.asyncio
async def test_create_raises_when_password_missing(async_mock_db: AsyncMock) -> None:
    with patch('backend.app.admin.service.user_service.user_dao') as dao:
        dao.get_by_username = AsyncMock(return_value=None)
        obj = AddUserParam(username='u', password='', roles=[1])
        with pytest.raises(errors.RequestError) as ei:
            await UserService.create(db=async_mock_db, obj=obj)
        assert ei.value.msg == 'error.password_required'


@pytest.mark.asyncio
async def test_create_raises_when_role_missing(async_mock_db: AsyncMock) -> None:
    with patch('backend.app.admin.service.user_service.user_dao') as dao:
        dao.get_by_username = AsyncMock(return_value=None)
        with patch('backend.app.admin.service.user_service.role_dao') as rdao:
            rdao.get = AsyncMock(return_value=None)
            obj = AddUserParam(username='u', password='secret', roles=[99])
            with pytest.raises(errors.NotFoundError) as ei:
                await UserService.create(db=async_mock_db, obj=obj)
            assert ei.value.msg == 'error.role_not_found'


@pytest.mark.asyncio
async def test_create_calls_add_when_valid(async_mock_db: AsyncMock) -> None:
    with patch('backend.app.admin.service.user_service.user_dao') as dao:
        dao.get_by_username = AsyncMock(return_value=None)
        dao.add = AsyncMock()
        with patch('backend.app.admin.service.user_service.role_dao') as rdao:
            rdao.get = AsyncMock(return_value=MagicMock())
            with patch('backend.app.admin.service.user_service.process_avatar_input', return_value=None):
                obj = AddUserParam(username='new', password='secret', roles=[1], nickname=None, avatar=None)
                await UserService.create(db=async_mock_db, obj=obj)
                dao.add.assert_awaited_once()
                adb, aobj = dao.add.await_args.args
                assert adb is async_mock_db
                assert aobj.username == 'new'
