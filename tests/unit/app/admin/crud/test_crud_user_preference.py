"""CRUDUserPreference.upsert 更新 / 插入分支。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.admin.crud.crud_user_preference import user_preference_dao
from backend.app.admin.model.user_preference import UserPreference
from backend.app.admin.schema.user_preference import UpdateUserPreferenceParam


@pytest.mark.asyncio
async def test_upsert_updates_existing_row() -> None:
    row = MagicMock(spec=UserPreference)
    row.locale = "en"
    row.theme = "auto"
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    obj = UpdateUserPreferenceParam(theme="dark")
    with patch.object(user_preference_dao, "get_by_user_id", new_callable=AsyncMock, return_value=row):
        out = await user_preference_dao.upsert(db, user_id=3, obj=obj)
        assert out is row
        assert row.theme == "dark"
        db.add.assert_called_once_with(row)
        db.flush.assert_awaited_once()
        db.refresh.assert_awaited_once_with(row)


@pytest.mark.asyncio
async def test_upsert_inserts_when_missing() -> None:
    db = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    obj = UpdateUserPreferenceParam(locale="zh", theme="light")
    captured: dict = {}

    def _capture_add(instance: UserPreference) -> None:
        captured["row"] = instance

    db.add = MagicMock(side_effect=_capture_add)

    with patch.object(user_preference_dao, "get_by_user_id", new_callable=AsyncMock, return_value=None):
        out = await user_preference_dao.upsert(db, user_id=9, obj=obj)
        assert out is captured["row"]
        assert captured["row"].user_id == 9
        assert captured["row"].locale == "zh"
        assert captured["row"].theme == "light"
        db.flush.assert_awaited_once()
        db.refresh.assert_awaited_once_with(captured["row"])
