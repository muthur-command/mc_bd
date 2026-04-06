"""CRUDUserPasswordHistory。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.admin.crud.crud_user_password_history import user_password_history_dao
from backend.app.admin.schema.user_password_history import CreateUserPasswordHistoryParam


@pytest.mark.asyncio
async def test_create_delegates() -> None:
    db = AsyncMock()
    obj = MagicMock(spec=CreateUserPasswordHistoryParam)
    with patch.object(user_password_history_dao, "create_model", new_callable=AsyncMock) as cm:
        await user_password_history_dao.create(db, obj)
        cm.assert_awaited_once_with(db, obj)


@pytest.mark.asyncio
async def test_get_by_user_id_delegates() -> None:
    db = AsyncMock()
    rows = [MagicMock()]
    with patch.object(user_password_history_dao, "select_models_order", new_callable=AsyncMock) as sm:
        sm.return_value = rows
        out = await user_password_history_dao.get_by_user_id(db, 42)
        assert out == rows
        sm.assert_awaited_once()
        args = sm.await_args.args
        assert args[0] is db
        assert args[1] == "id"
        assert args[2] == "desc"
