"""用户偏好表：语言、主题、侧边栏、通知等前端配置"""

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key


class UserPreference(Base):
    """用户偏好表，与用户一对一"""

    __tablename__ = 'sys_user_preference'

    id: Mapped[id_key] = mapped_column(init=False)
    user_id: Mapped[int] = mapped_column(sa.BigInteger, unique=True, index=True, comment='用户 ID')
    locale: Mapped[str] = mapped_column(sa.String(16), default='en', comment='语言 zh/en')
    theme: Mapped[str] = mapped_column(sa.String(16), default='auto', comment='主题 light/dark/auto')
    theme_color: Mapped[str] = mapped_column(
        sa.String(32), default='lake-view', comment='颜色预设 default/lake-view/...'
    )
    radius: Mapped[str] = mapped_column(sa.String(16), default='xl', comment='圆角 none/sm/md/lg/xl')
    scale: Mapped[str] = mapped_column(sa.String(16), default='sm', comment='缩放 none/sm/lg')
    content_layout: Mapped[str] = mapped_column(sa.String(16), default='full', comment='内容布局 full/centered')
    sidebar_collapsed: Mapped[bool] = mapped_column(default=False, comment='侧边栏是否折叠')
    plugin_system_show_remote: Mapped[bool] = mapped_column(default=False, comment='插件管理页是否显示远程列表')
    profile_cover: Mapped[str | None] = mapped_column(
        sa.String(500), default=None, comment='个人资料页背景图路径，同头像存 /static/upload/cover/xxx'
    )
