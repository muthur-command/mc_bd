"""用户偏好 CRUD"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.user_preference import UserPreference
from backend.app.admin.schema.user_preference import UpdateUserPreferenceParam


class CRUDUserPreference(CRUDPlus[UserPreference]):
    """用户偏好数据库操作"""

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> UserPreference | None:
        """按用户 ID 获取偏好"""
        return await self.select_model_by_column(db, user_id=user_id)

    async def upsert(
        self, db: AsyncSession, user_id: int, obj: UpdateUserPreferenceParam
    ) -> UserPreference:
        """存在则更新，否则插入"""
        row = await self.get_by_user_id(db, user_id)
        data = obj.model_dump(exclude_none=True)
        if row:
            for k, v in data.items():
                setattr(row, k, v)
            db.add(row)
            await db.flush()
            await db.refresh(row)
            return row
        full = {
            'user_id': user_id,
            'locale': data.get('locale', 'en'),
            'theme': data.get('theme', 'auto'),
            'theme_color': data.get('theme_color', 'lake-view'),
            'radius': data.get('radius', 'xl'),
            'scale': data.get('scale', 'sm'),
            'content_layout': data.get('content_layout', 'full'),
            'sidebar_collapsed': data.get('sidebar_collapsed', False),
            'plugin_system_show_remote': data.get('plugin_system_show_remote', False),
            'profile_cover': data.get('profile_cover'),
        }
        new_row = UserPreference(**full)
        db.add(new_row)
        await db.flush()
        await db.refresh(new_row)
        return new_row


user_preference_dao = CRUDUserPreference(UserPreference)
