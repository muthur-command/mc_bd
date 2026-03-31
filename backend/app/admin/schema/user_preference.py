"""用户偏好 Schema"""

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class UserPreferenceSchema(SchemaBase):
    """用户偏好：用于返回与更新"""

    model_config = ConfigDict(from_attributes=True)

    locale: str = Field(default='en', description='语言 zh/en')
    theme: str = Field(default='auto', description='主题 light/dark/auto')
    # 以下为可选：DB 为 NULL 时返回 null，前端不应用以免覆盖本地/已保存的配置
    theme_color: str | None = Field(None, description='颜色预设')
    radius: str | None = Field(None, description='圆角 none/sm/md/lg/xl')
    scale: str | None = Field(None, description='缩放 none/sm/lg')
    content_layout: str | None = Field(None, description='内容布局 full/centered')
    sidebar_collapsed: bool = Field(default=False, description='侧边栏是否折叠')
    plugin_system_show_remote: bool = Field(default=False, description='插件管理页是否显示远程列表')
    profile_cover: str | None = Field(None, description='个人资料页背景图路径')

class UpdateUserPreferenceParam(UserPreferenceSchema):
    """更新用户偏好参数：全部可选"""

    locale: str | None = Field(None, description='语言')
    theme: str | None = Field(None, description='主题')
    theme_color: str | None = Field(None, description='颜色预设')
    radius: str | None = Field(None, description='圆角')
    scale: str | None = Field(None, description='缩放')
    content_layout: str | None = Field(None, description='内容布局')
    sidebar_collapsed: bool | None = Field(None, description='侧边栏是否折叠')
    plugin_system_show_remote: bool | None = Field(None, description='插件管理页是否显示远程列表')
    profile_cover: str | None = Field(None, description='个人资料页背景图路径或 data URI')
