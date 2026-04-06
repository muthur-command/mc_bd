"""CRUDUser：复杂 add/update/delete 与委托方法。"""

from collections.abc import Callable, Sequence
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sqlalchemy import Select

from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.schema.user import AddUserParam, UpdateUserParam


@pytest.mark.asyncio
async def test_get_select_returns_select() -> None:
    sel = await user_dao.get_select('u', 'e@x.com', 1)
    assert isinstance(sel, Select)


@pytest.mark.asyncio
async def test_get_select_skips_empty_username() -> None:
    sel = await user_dao.get_select('', None, None)
    assert isinstance(sel, Select)


@pytest.mark.asyncio
async def test_add_hashes_password_and_links_roles(
    async_mock_db_with_flush: AsyncMock,
    sqlalchemy_scalar_rows_factory: Callable[[Sequence[object]], MagicMock],
) -> None:
    plain = 'secret123'
    obj = AddUserParam(username='tuser', password=plain, roles=[10])

    def _assign_id(user_obj: object) -> None:
        user_obj.id = 55

    async_mock_db_with_flush.add = MagicMock(side_effect=_assign_id)
    role_row = MagicMock()
    role_row.id = 10
    async_mock_db_with_flush.execute = AsyncMock(return_value=sqlalchemy_scalar_rows_factory([role_row]))

    await user_dao.add(async_mock_db_with_flush, obj)

    assert obj.password != plain
    async_mock_db_with_flush.add.assert_called_once()
    new_user = async_mock_db_with_flush.add.call_args[0][0]
    assert new_user.username == 'tuser'
    async_mock_db_with_flush.flush.assert_awaited_once()
    assert async_mock_db_with_flush.execute.await_count >= 2


@pytest.mark.asyncio
async def test_update_refreshes_roles() -> None:
    uobj = UpdateUserParam(
        username='u',
        nickname='n',
        avatar=None,
        email=None,
        phone=None,
        roles=[2],
    )
    db = AsyncMock()
    role_row = MagicMock()
    role_row.id = 2
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [role_row]
    db.execute = AsyncMock(return_value=mock_result)

    with patch.object(user_dao, 'update_model', new_callable=AsyncMock, return_value=1) as um:
        n = await user_dao.update(db, 5, uobj)
        assert n == 1
        um.assert_awaited_once()
        assert db.execute.await_count >= 3


@pytest.mark.asyncio
async def test_reset_password_updates_hash_and_salt() -> None:
    db = AsyncMock()
    with patch.object(user_dao, 'update_model', new_callable=AsyncMock, return_value=1) as um:
        await user_dao.reset_password(db, 8, 'new-pass')
        um.assert_awaited_once()
        _db, pk, payload = um.await_args.args
        assert pk == 8
        assert 'password' in payload and 'salt' in payload
        assert payload['password'] != 'new-pass'


@pytest.mark.asyncio
async def test_delete_clears_user_role_and_user() -> None:
    db = AsyncMock()
    db.execute = AsyncMock()
    with patch('backend.app.admin.crud.crud_user.import_module_cached', side_effect=ImportError):
        with patch.object(user_dao, 'delete_model', new_callable=AsyncMock, return_value=1) as dm:
            n = await user_dao.delete(db, 100)
            assert n == 1
            db.execute.assert_awaited()
            dm.assert_awaited_once_with(db, 100)


@pytest.mark.asyncio
async def test_get_join_uses_select_models_and_serialize() -> None:
    db = AsyncMock()
    with patch.object(user_dao, 'select_models', new_callable=AsyncMock, return_value=[]) as sm:
        with patch('backend.app.admin.crud.crud_user.select_join_serialize', return_value={'id': 1}) as sjs:
            out = await user_dao.get_join(db, user_id=1)
            assert out == {'id': 1}
            sm.assert_awaited_once()
            sjs.assert_called_once()


@pytest.mark.asyncio
async def test_update_login_time_delegates() -> None:
    db = AsyncMock()
    with patch.object(user_dao, 'update_model_by_column', new_callable=AsyncMock, return_value=1) as um:
        with patch('backend.app.admin.crud.crud_user.timezone') as tz:
            now = object()
            tz.now.return_value = now
            n = await user_dao.update_login_time(db, 'admin')
            assert n == 1
            um.assert_awaited_once_with(db, {'last_login_time': now}, username='admin')


@pytest.mark.asyncio
async def test_set_super_staff_status_multi_login_delegate() -> None:
    db = AsyncMock()
    with patch.object(user_dao, 'update_model', new_callable=AsyncMock, return_value=1) as um:
        await user_dao.set_super(db, 1, is_super=True)
        um.assert_awaited_with(db, 1, {'is_superuser': True})
        await user_dao.set_staff(db, 2, is_staff=False)
        um.assert_awaited_with(db, 2, {'is_staff': False})
        await user_dao.set_status(db, 3, 0)
        um.assert_awaited_with(db, 3, {'status': 0})
        await user_dao.set_multi_login(db, 4, multi_login=True)
        um.assert_awaited_with(db, 4, {'is_multi_login': True})
