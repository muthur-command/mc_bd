"""AuthService 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.admin.service.auth_service import AuthService
from backend.common.exception import errors


@pytest.mark.asyncio
async def test_user_verify_raises_when_user_missing() -> None:
    svc = AuthService()
    with patch('backend.app.admin.service.auth_service.user_dao') as dao:
        dao.get_by_username = AsyncMock(return_value=None)
        db = AsyncMock()
        with pytest.raises(errors.RequestError) as ei:
            await svc.user_verify(db, 'nouser', 'pw')
        assert ei.value.msg == 'error.username_not_found'


@pytest.mark.asyncio
async def test_user_verify_raises_on_wrong_password() -> None:
    svc = AuthService()
    user = MagicMock()
    user.id = 1
    user.password = 'hash'
    user.status = 1
    with patch('backend.app.admin.service.auth_service.user_dao') as dao:
        dao.get_by_username = AsyncMock(return_value=user)
        with patch('backend.app.admin.service.auth_service.password_security_service') as sec:
            sec.check_status = AsyncMock()
            sec.check_password_expiry_status = AsyncMock(return_value=None)
            sec.handle_login_success = AsyncMock()
            sec.handle_login_failure = AsyncMock()
            with patch('backend.app.admin.service.auth_service.password_verify', return_value=False):
                db = AsyncMock()
                with pytest.raises(errors.AuthorizationError):
                    await svc.user_verify(db, 'u', 'wrong')
                sec.handle_login_failure.assert_awaited_once_with(db, 1)


@pytest.mark.asyncio
async def test_user_verify_success() -> None:
    svc = AuthService()
    user = MagicMock()
    user.id = 7
    user.password = 'hash'
    user.status = 1
    with patch('backend.app.admin.service.auth_service.user_dao') as dao:
        dao.get_by_username = AsyncMock(return_value=user)
        with patch('backend.app.admin.service.auth_service.password_security_service') as sec:
            sec.check_status = AsyncMock()
            sec.check_password_expiry_status = AsyncMock(return_value=3)
            sec.handle_login_success = AsyncMock()
            with patch('backend.app.admin.service.auth_service.password_verify', return_value=True):
                db = AsyncMock()
                u, days = await svc.user_verify(db, 'u', 'ok')
                assert u is user
                assert days == 3


@pytest.mark.asyncio
async def test_get_codes_returns_empty() -> None:
    db = AsyncMock()
    req = MagicMock()
    codes = await AuthService.get_codes(db=db, request=req)
    assert codes == []
