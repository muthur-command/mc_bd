"""UserPasswordHistoryService（登录失败 / 锁定 / 密码过期）单元测试。"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.admin.service.user_password_history_service import password_security_service
from backend.common.exception import errors
from backend.core.conf import settings
from backend.utils.timezone import timezone


@pytest.mark.asyncio
async def test_check_status_raises_when_user_disabled() -> None:
    with pytest.raises(errors.AuthorizationError) as ei:
        await password_security_service.check_status(user_id=1, user_status=0)
    assert ei.value.msg == '用户已被锁定, 请联系统管理员'


@pytest.mark.asyncio
async def test_check_status_passes_when_active_and_no_redis_lock() -> None:
    with patch('backend.app.admin.service.user_password_history_service.redis_client') as redis:
        redis.get = AsyncMock(return_value=None)
        await password_security_service.check_status(user_id=1, user_status=1)
        redis.get.assert_awaited()


@pytest.mark.asyncio
async def test_handle_login_failure_increments_until_lock() -> None:
    db = AsyncMock()
    with patch(
        'backend.app.admin.service.user_password_history_service.load_user_security_config', new_callable=AsyncMock
    ):
        with patch('backend.app.admin.service.user_password_history_service.redis_client') as redis:
            with patch.object(settings, 'USER_LOCK_THRESHOLD', 2), patch.object(settings, 'USER_LOCK_SECONDS', 60):
                redis.get = AsyncMock(side_effect=[None, '1'])
                redis.set = AsyncMock()
                await password_security_service.handle_login_failure(db, 99)
                with pytest.raises(errors.AuthorizationError) as ei:
                    await password_security_service.handle_login_failure(db, 99)
                assert ei.value.msg == '登录失败次数过多，账号已被锁定'


@pytest.mark.asyncio
async def test_handle_login_success_clears_redis_keys() -> None:
    with patch('backend.app.admin.service.user_password_history_service.redis_client') as redis:
        redis.delete = AsyncMock()
        await password_security_service.handle_login_success(3)
        assert redis.delete.await_count == 2


@pytest.mark.asyncio
async def test_check_password_expiry_disabled_returns_none() -> None:
    db = AsyncMock()
    with patch(
        'backend.app.admin.service.user_password_history_service.load_user_security_config', new_callable=AsyncMock
    ):
        with patch.object(settings, 'USER_PASSWORD_EXPIRY_DAYS', 0):
            out = await password_security_service.check_password_expiry_status(db, datetime.now())
            assert out is None


@pytest.mark.asyncio
async def test_check_password_expiry_raises_when_never_changed() -> None:
    db = AsyncMock()
    with patch(
        'backend.app.admin.service.user_password_history_service.load_user_security_config', new_callable=AsyncMock
    ):
        with patch.object(settings, 'USER_PASSWORD_EXPIRY_DAYS', 90):
            with pytest.raises(errors.AuthorizationError) as ei:
                await password_security_service.check_password_expiry_status(db, None)
            assert ei.value.msg == '密码已过期，请修改密码后重新登录'


@pytest.mark.asyncio
async def test_check_password_expiry_returns_days_when_near() -> None:
    db = AsyncMock()
    changed = datetime(2030, 1, 1, 12, 0, 0)
    with patch(
        'backend.app.admin.service.user_password_history_service.load_user_security_config', new_callable=AsyncMock
    ):
        with (
            patch.object(settings, 'USER_PASSWORD_EXPIRY_DAYS', 100),
            patch.object(settings, 'USER_PASSWORD_REMINDER_DAYS', 30),
        ):
            with patch.object(timezone, 'now', return_value=changed + timedelta(days=75)):
                out = await password_security_service.check_password_expiry_status(db, changed)
                assert out == 25
