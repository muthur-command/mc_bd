from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.enums import StatusType
from backend.common.schema import SchemaBase


class RoleSchemaBase(SchemaBase):
    """角色基础模型"""

    name: str = Field(description='角色名称')
    status: StatusType = Field(description='状态')
    remark: str | None = Field(None, description='备注')


class CreateRoleParam(RoleSchemaBase):
    """创建角色参数"""


class UpdateRoleParam(RoleSchemaBase):
    """更新角色参数"""


class DeleteRoleParam(SchemaBase):
    """删除角色参数"""

    pks: list[int] = Field(description='角色 ID 列表')


class GetRoleDetail(RoleSchemaBase):
    """角色详情"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='角色 ID')
    created_time: datetime = Field(description='创建时间')
    updated_time: datetime | None = Field(None, description='更新时间')
