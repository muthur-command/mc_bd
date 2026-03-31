from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field, model_validator
from typing_extensions import Self

from backend.app.admin.schema.role import GetRoleDetail
from backend.common.enums import StatusType
from backend.common.schema import CustomEmailStr, CustomPhoneNumber, SchemaBase
from backend.core.conf import settings

# 支持 base64 data URI 时的最大长度（约 5MB 图片的 base64）
AVATAR_INPUT_MAX_LENGTH = int(settings.UPLOAD_IMAGE_SIZE_MAX * 4 / 3) + 1024


class AuthSchemaBase(SchemaBase):
    """用户认证基础模型"""

    username: str = Field(description='用户名')
    password: str = Field(description='密码')


class AuthLoginParam(AuthSchemaBase):
    """用户登录参数"""

    uuid: str | None = Field(None, description='验证码 UUID')
    captcha: str | None = Field(None, description='验证码')


class AddUserParam(AuthSchemaBase):
    """添加用户参数"""

    nickname: str | None = Field(None, description='昵称')
    avatar: str | None = Field(None, max_length=AVATAR_INPUT_MAX_LENGTH, description='头像：URL 或 data URI（Boring 生成 / 本地上传）')
    email: CustomEmailStr | None = Field(None, description='邮箱')
    phone: CustomPhoneNumber | None = Field(None, description='手机号码')
    roles: list[int] = Field(description='角色 ID 列表')


class AddUserRoleParam(SchemaBase):
    """添加用户角色"""

    user_id: int = Field(description='用户 ID')
    role_id: int = Field(description='角色 ID')


class AddOAuth2UserParam(AuthSchemaBase):
    """添加 OAuth2 用户参数"""

    password: str | None = Field(None, description='密码')
    nickname: str | None = Field(None, description='昵称')
    email: CustomEmailStr | None = Field(None, description='邮箱')
    avatar: str | None = Field(None, max_length=AVATAR_INPUT_MAX_LENGTH, description='头像 URL 或 data URI')


class ResetPasswordParam(SchemaBase):
    """重置密码参数"""

    old_password: str = Field(description='旧密码')
    new_password: str = Field(description='新密码')
    confirm_password: str = Field(description='确认密码')


class UserInfoSchemaBase(SchemaBase):
    """用户信息基础模型"""

    username: str = Field(description='用户名')
    nickname: str = Field(description='昵称')
    avatar: str | None = Field(None, max_length=AVATAR_INPUT_MAX_LENGTH, description='头像：URL 或 data URI')
    email: CustomEmailStr | None = Field(None, description='邮箱')
    phone: CustomPhoneNumber | None = Field(None, description='手机号')


class UpdateUserParam(UserInfoSchemaBase):
    """更新用户参数"""

    roles: list[int] = Field(description='角色 ID 列表')


class GetUserInfoDetail(UserInfoSchemaBase):
    """用户信息详情"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='用户 ID')
    uuid: str = Field(description='用户 UUID')
    status: StatusType = Field(description='状态')
    is_superuser: bool = Field(description='是否超级管理员')
    is_staff: bool = Field(description='是否管理员')
    is_multi_login: bool = Field(description='是否允许多端登录')
    join_time: datetime = Field(description='加入时间')
    last_login_time: datetime | None = Field(None, description='最后登录时间')


class GetUserInfoWithRelationDetail(GetUserInfoDetail):
    """用户信息关联详情"""

    model_config = ConfigDict(from_attributes=True)

    roles: list[GetRoleDetail] = Field(description='角色列表')


class GetCurrentUserInfoWithRelationDetail(GetUserInfoWithRelationDetail):
    """当前用户信息关联详情"""

    model_config = ConfigDict(from_attributes=True)

    roles: list[str] = Field(description='角色名称列表')

    @model_validator(mode='before')
    @classmethod
    def handel(cls, data: Any) -> Self:
        """处理角色数据"""
        roles = data.get('roles')
        if roles:
            data['roles'] = [role['name'] for role in roles]
        return data
