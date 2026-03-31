from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_role import role_dao
from backend.app.admin.model import Role
from backend.app.admin.schema.role import CreateRoleParam, DeleteRoleParam, UpdateRoleParam
from backend.app.admin.utils.cache import user_cache_manager
from backend.common.exception import errors
from backend.common.pagination import paging_data


class RoleService:
    """角色服务类"""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> Role:
        """
        获取角色详情

        :param db: 数据库会话
        :param pk: 角色 ID
        :return:
        """

        role = await role_dao.get(db, pk)
        if not role:
            raise errors.NotFoundError(msg='角色不存在')
        return role

    @staticmethod
    async def get_all(*, db: AsyncSession) -> Sequence[Role]:
        """
        获取所有角色

        :param db: 数据库会话
        :return:
        """

        roles = await role_dao.get_all(db)
        return roles

    @staticmethod
    async def get_list(*, db: AsyncSession, name: str | None, status: int | None) -> dict[str, Any]:
        """
        获取角色列表

        :param db: 数据库会话
        :param name: 角色名称
        :param status: 状态
        :return:
        """
        role_select = await role_dao.get_select(name=name, status=status)
        return await paging_data(db, role_select)

    @staticmethod
    async def create(*, db: AsyncSession, obj: CreateRoleParam) -> None:
        """
        创建角色

        :param db: 数据库会话
        :param obj: 角色创建参数
        :return:
        """

        role = await role_dao.get_by_name(db, obj.name)
        if role:
            raise errors.ConflictError(msg='角色已存在')
        await role_dao.create(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateRoleParam) -> int:
        """
        更新角色

        :param db: 数据库会话
        :param pk: 角色 ID
        :param obj: 角色更新参数
        :return:
        """

        role = await role_dao.get(db, pk)
        if not role:
            raise errors.NotFoundError(msg='角色不存在')
        if role.name != obj.name and await role_dao.get_by_name(db, obj.name):
            raise errors.ConflictError(msg='角色已存在')
        count = await role_dao.update(db, pk, obj)
        await user_cache_manager.clear_by_role_id(db, [pk])
        return count

    @staticmethod
    async def delete(*, db: AsyncSession, obj: DeleteRoleParam) -> int:
        """
        批量删除角色

        :param db: 数据库会话
        :param obj: 角色 ID 列表
        :return:
        """

        count = await role_dao.delete(db, obj.pks)
        await user_cache_manager.clear_by_role_id(db, obj.pks)
        return count


role_service: RoleService = RoleService()
