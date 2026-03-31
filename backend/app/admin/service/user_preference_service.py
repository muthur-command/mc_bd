"""用户偏好服务"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_user_preference import user_preference_dao
from backend.app.admin.schema.user_preference import UpdateUserPreferenceParam, UserPreferenceSchema
from backend.app.admin.utils.avatar import process_cover_input, remove_upload_file_if_local


class UserPreferenceService:
    """用户偏好服务"""

    @staticmethod
    async def get_preferences(db: AsyncSession, user_id: int) -> UserPreferenceSchema:
        """获取用户偏好，不存在则返回默认值"""
        row = await user_preference_dao.get_by_user_id(db, user_id)
        if row:
            return UserPreferenceSchema.model_validate(row)
        return UserPreferenceSchema()

    @staticmethod
    async def save_preferences(
        db: AsyncSession, user_id: int, obj: UpdateUserPreferenceParam
    ) -> UserPreferenceSchema:
        """保存用户偏好（存在则更新，否则创建）；profile_cover 为 data URI 时先落盘再存路径"""
        row = await user_preference_dao.get_by_user_id(db, user_id)
        old_cover = row.profile_cover if row else None
        if obj.profile_cover is not None and str(obj.profile_cover).strip().startswith('data:image/'):
            obj = obj.model_copy(update={'profile_cover': process_cover_input(obj.profile_cover, user_id)})
        row = await user_preference_dao.upsert(db, user_id, obj)
        if row and old_cover and old_cover != (row.profile_cover or ''):
            remove_upload_file_if_local(old_cover, allowed_subdirs=('cover',))
        await db.commit()
        return UserPreferenceSchema.model_validate(row)


user_preference_service = UserPreferenceService()
