from collections.abc import Sequence
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_role import role_dao
from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.model import Role, User
from backend.app.admin.schema.user import (
    AddUserParam,
    ResetPasswordParam,
    UpdateUserParam,
)
from backend.app.admin.schema.user_password_history import CreateUserPasswordHistoryParam
from backend.app.admin.service.user_password_history_service import password_security_service
from backend.app.admin.utils.avatar import (
    process_avatar_input,
    remove_upload_file_if_local,
)
from backend.app.admin.utils.password_security import password_verify, validate_new_password
from backend.common.context import ctx
from backend.common.enums import UserPermissionType
from backend.common.exception import errors
from backend.common.pagination import paging_data
from backend.common.response.response_code import CustomErrorCode
from backend.common.security.jwt import get_token, jwt_decode
from backend.core.conf import settings
from backend.database.redis import redis_client
from backend.utils.serializers import select_join_serialize


class UserService:
    """用户服务类"""

    @staticmethod
    async def get_userinfo(*, db: AsyncSession, pk: int | None = None, username: str | None = None) -> User:
        """
        获取用户信息

        :param db: 数据库会话
        :param pk: 用户 ID
        :param username: 用户名
        :return:
        """
        user = await user_dao.get_join(db, user_id=pk, username=username)
        if not user:
            raise errors.NotFoundError(msg='error.user_not_found')
        return user

    @staticmethod
    async def get_roles(*, db: AsyncSession, pk: int) -> Sequence[Role]:
        """
        获取用户所有角色

        :param db: 数据库会话
        :param pk: 用户 ID
        :return:
        """
        user = await user_dao.get_join(db, user_id=pk)
        if not user:
            raise errors.NotFoundError(msg='error.user_not_found')
        return user.roles

    @staticmethod
    async def get_list(*, db: AsyncSession, username: str, email: str, status: int) -> dict[str, Any]:
        """
        获取用户列表

        :param db: 数据库会话
        :param username: 用户名
        :param email: 邮箱
        :param status: 状态
        :return:
        """
        user_select = await user_dao.get_select(username=username, email=email, status=status)
        data = await paging_data(db, user_select)
        if data['items']:
            serialized_items = select_join_serialize(
                data['items'],
                relationships=['User-m2m-Role'],
                return_as_dict=True,
            )
            # 确保返回的是列表，即使只有一个元素
            data['items'] = [serialized_items] if not isinstance(serialized_items, list) else serialized_items
        return data

    @staticmethod
    async def create(*, db: AsyncSession, obj: AddUserParam) -> None:
        """
        创建用户

        :param db: 数据库会话
        :param obj: 用户添加参数
        :return:
        """
        if await user_dao.get_by_username(db, obj.username):
            raise errors.ConflictError(msg='error.username_exists')
        if not obj.password:
            raise errors.RequestError(msg='error.password_required')
        for role_id in obj.roles:
            if not await role_dao.get(db, role_id):
                raise errors.NotFoundError(msg='error.role_not_found')
        obj.nickname = obj.nickname or obj.username
        if obj.avatar:
            obj.avatar = process_avatar_input(obj.avatar, 0)
        await user_dao.add(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateUserParam) -> int:
        """
        更新用户信息

        :param db: 数据库会话
        :param pk: 用户 ID
        :param obj: 用户更新参数
        :return:
        """
        user = await user_dao.get_join(db, user_id=pk)
        if not user:
            raise errors.NotFoundError(msg='error.user_not_found')
        if obj.username != user.username and await user_dao.get_by_username(db, obj.username):
            raise errors.ConflictError(msg='error.username_exists')
        for role_id in obj.roles:
            if not await role_dao.get(db, role_id):
                raise errors.NotFoundError(msg='error.role_not_found')
        old_avatar = user.avatar if obj.avatar is not None else None
        if obj.avatar is not None:
            obj.avatar = process_avatar_input(obj.avatar, user.id)
        count = await user_dao.update(db, user.id, obj)
        if count > 0 and old_avatar is not None and old_avatar != (obj.avatar or ''):
            remove_upload_file_if_local(old_avatar, allowed_subdirs=('avatar',))
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user.id}')
        return count

    @staticmethod
    async def update_permission(*, db: AsyncSession, request: Request, pk: int, type: UserPermissionType) -> int:  # noqa: C901
        """
        更新用户权限

        :param db: 数据库会话
        :param request: FastAPI 请求对象
        :param pk: 用户 ID
        :param type: 权限类型
        :return:
        """
        match type:
            case UserPermissionType.superuser:
                user = await user_dao.get(db, pk)
                if not user:
                    raise errors.NotFoundError(msg='error.user_not_found')
                if pk == request.user.id:
                    raise errors.ForbiddenError(msg='error.forbidden_modify_self_permission')
                count = await user_dao.set_super(db, pk, is_super=not user.is_superuser)
            case UserPermissionType.staff:
                user = await user_dao.get(db, pk)
                if not user:
                    raise errors.NotFoundError(msg='error.user_not_found')
                if pk == request.user.id:
                    raise errors.ForbiddenError(msg='error.forbidden_modify_self_permission')
                count = await user_dao.set_staff(db, pk, is_staff=not user.is_staff)
            case UserPermissionType.status:
                user = await user_dao.get(db, pk)
                if not user:
                    raise errors.NotFoundError(msg='error.user_not_found')
                if pk == request.user.id:
                    raise errors.ForbiddenError(msg='error.forbidden_modify_self_permission')
                count = await user_dao.set_status(db, pk, 0 if user.status == 1 else 1)
            case UserPermissionType.multi_login:
                user = await user_dao.get(db, pk)
                if not user:
                    raise errors.NotFoundError(msg='error.user_not_found')
                multi_login = user.is_multi_login if pk != user.id else request.user.is_multi_login
                new_multi_login = not multi_login
                count = await user_dao.set_multi_login(db, pk, multi_login=new_multi_login)
                token = get_token(request)
                token_payload = jwt_decode(token)
                if pk == user.id:
                    # 系统管理员修改自身时，除当前 token 外，其他 token 失效
                    if not new_multi_login:
                        key_prefix = f'{settings.TOKEN_REDIS_PREFIX}:{user.id}'
                        await redis_client.delete_prefix(
                            key_prefix,
                            exclude=f'{key_prefix}:{token_payload.session_uuid}',
                        )
                else:
                    # 系统管理员修改他人时，他人 token 全部失效
                    if not new_multi_login:
                        key_prefix = f'{settings.TOKEN_REDIS_PREFIX}:{user.id}'
                        await redis_client.delete_prefix(key_prefix)
            case _:
                raise errors.RequestError(msg='error.permission_type_not_found')

        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user.id}')
        return count

    @staticmethod
    async def reset_password(*, db: AsyncSession, pk: int, password: str) -> int:
        """
        重置用户密码

        :param db: 数据库会话
        :param pk: 用户 ID
        :param password: 新密码
        :return:
        """
        user = await user_dao.get(db, pk)
        if not user:
            raise errors.NotFoundError(msg='error.user_not_found')

        await validate_new_password(db, user.id, password)
        count = await user_dao.reset_password(db, user.id, password)

        history_obj = CreateUserPasswordHistoryParam(user_id=user.id, password=user.password)
        await password_security_service.save_password_history(db, history_obj)
        await user_dao.update_password_changed_time(db, user.id)

        key_prefix = [
            f'{settings.TOKEN_REDIS_PREFIX}:{user.id}',
            f'{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user.id}',
            f'{settings.JWT_USER_REDIS_PREFIX}:{user.id}',
        ]
        for prefix in key_prefix:
            await redis_client.delete(prefix)
        return count

    @staticmethod
    async def update_nickname(*, db: AsyncSession, user_id: int, nickname: str) -> int:
        """
        更新当前用户昵称

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param nickname: 用户昵称
        :return:
        """
        count = await user_dao.update_nickname(db, user_id, nickname)
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user_id}')
        return count

    @staticmethod
    async def update_avatar(*, db: AsyncSession, user_id: int, avatar: str) -> tuple[int, str | None]:
        """
        更新当前用户头像

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param avatar: 头像地址或 base64 data URI
        :return: (更新行数, 写入库的头像 URL，供前端立即刷新)
        """
        user = await user_dao.get(db, user_id)
        old_avatar = user.avatar if user else None
        avatar_url = process_avatar_input(avatar, user_id)
        stored = avatar_url if avatar_url is not None else ''
        count = await user_dao.update_avatar(db, user_id, stored)
        if count > 0 and old_avatar and old_avatar != stored:
            remove_upload_file_if_local(old_avatar, allowed_subdirs=('avatar',))
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user_id}')
        return count, (avatar_url if count else None)

    @staticmethod
    async def update_email(*, db: AsyncSession, user_id: int, captcha: str, email: str) -> int:
        """
        更新当前用户邮箱

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param captcha: 邮箱验证码
        :param email: 邮箱
        :return:
        """
        captcha_code = await redis_client.get(f'{settings.EMAIL_CAPTCHA_REDIS_PREFIX}:{ctx.ip}')
        if not captcha_code:
            raise errors.RequestError(msg='error.captcha_expired')
        if captcha != captcha_code:
            raise errors.CustomError(error=CustomErrorCode.CAPTCHA_ERROR)
        await redis_client.delete(f'{settings.EMAIL_CAPTCHA_REDIS_PREFIX}:{ctx.ip}')
        count = await user_dao.update_email(db, user_id, email)
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user_id}')
        return count

    @staticmethod
    async def update_password(*, db: AsyncSession, user_id: int, obj: ResetPasswordParam) -> int:
        """
        更新当前用户密码

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param obj: 密码重置参数
        :return:
        """
        user = await user_dao.get(db, user_id)

        if user.password and not password_verify(obj.old_password, user.password):
            raise errors.RequestError(msg='error.old_password_wrong')

        if obj.new_password != obj.confirm_password:
            raise errors.RequestError(msg='error.password_mismatch')

        await validate_new_password(db, user_id, obj.new_password)
        count = await user_dao.reset_password(db, user_id, obj.new_password)

        history_obj = CreateUserPasswordHistoryParam(user_id=user.id, password=user.password)
        await password_security_service.save_password_history(db, history_obj)
        await user_dao.update_password_changed_time(db, user.id)

        key_prefix = [
            f'{settings.TOKEN_REDIS_PREFIX}:{user_id}',
            f'{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}',
            f'{settings.JWT_USER_REDIS_PREFIX}:{user_id}',
        ]
        for prefix in key_prefix:
            await redis_client.delete_prefix(prefix)
        return count

    @staticmethod
    async def delete(*, db: AsyncSession, pk: int) -> int:
        """
        删除用户

        :param db: 数据库会话
        :param pk: 用户 ID
        :return:
        """
        user = await user_dao.get(db, pk)
        if not user:
            raise errors.NotFoundError(msg='error.user_not_found')
        count = await user_dao.delete(db, user.id)
        key_prefix = [
            f'{settings.TOKEN_REDIS_PREFIX}:{user.id}',
            f'{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user.id}',
        ]
        for key in key_prefix:
            await redis_client.delete_prefix(key)
        return count


user_service: UserService = UserService()
