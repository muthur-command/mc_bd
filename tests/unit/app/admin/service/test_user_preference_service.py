"""UserPreferenceService 单元测试。"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.admin.schema.user_preference import UpdateUserPreferenceParam
from backend.app.admin.service.user_preference_service import UserPreferenceService


@pytest.mark.asyncio
async def test_get_preferences_returns_defaults_when_no_row() -> None:
    with patch('backend.app.admin.service.user_preference_service.user_preference_dao') as dao:
        dao.get_by_user_id = AsyncMock(return_value=None)
        db = AsyncMock()
        schema = await UserPreferenceService.get_preferences(db, user_id=1)
        assert schema.locale == 'en'
        assert schema.theme == 'auto'


@pytest.mark.asyncio
async def test_get_preferences_validates_row() -> None:
    row = SimpleNamespace(
        locale='zh',
        theme='light',
        theme_color=None,
        radius=None,
        scale=None,
        content_layout=None,
        sidebar_collapsed=True,
        plugin_system_show_remote=True,
        profile_cover='/static/x.png',
    )
    with patch('backend.app.admin.service.user_preference_service.user_preference_dao') as dao:
        dao.get_by_user_id = AsyncMock(return_value=row)
        db = AsyncMock()
        schema = await UserPreferenceService.get_preferences(db, user_id=2)
        assert schema.locale == 'zh'
        assert schema.theme == 'light'
        assert schema.sidebar_collapsed is True


@pytest.mark.asyncio
async def test_save_preferences_upserts_and_commits() -> None:
    row_out = SimpleNamespace(
        locale='zh',
        theme='dark',
        theme_color=None,
        radius=None,
        scale=None,
        content_layout=None,
        sidebar_collapsed=False,
        plugin_system_show_remote=False,
        profile_cover=None,
    )
    with patch('backend.app.admin.service.user_preference_service.user_preference_dao') as dao:
        dao.get_by_user_id = AsyncMock(return_value=None)
        dao.upsert = AsyncMock(return_value=row_out)
        db = AsyncMock()
        db.commit = AsyncMock()
        obj = UpdateUserPreferenceParam(locale='zh', theme='dark')
        schema = await UserPreferenceService.save_preferences(db, user_id=5, obj=obj)
        assert schema.locale == 'zh'
        dao.upsert.assert_awaited_once()
        db.commit.assert_awaited_once()
