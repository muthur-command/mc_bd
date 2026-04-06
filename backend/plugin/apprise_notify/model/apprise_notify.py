"""Apprise 通道与发送历史表"""

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, UniversalText, id_key


class AppriseNotifyChannelRecord(Base):
    """Apprise 通知通道（一条记录对应一个 Apprise URL）"""

    __tablename__ = 'plugin_apprise_notify_channel'
    __table_args__ = {'comment': 'Apprise 通知通道'}

    id: Mapped[id_key] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(sa.String(128), comment='显示名称')
    apprise_url: Mapped[str] = mapped_column(UniversalText, comment='Apprise URL')
    enabled: Mapped[bool] = mapped_column(default=True, comment='是否启用')
    description: Mapped[str | None] = mapped_column(sa.String(512), default=None, comment='备注')


class AppriseNotifyLogRecord(Base):
    """通知发送历史（按通道逐条记录）"""

    __tablename__ = 'plugin_apprise_notify_log'
    __table_args__ = {'comment': 'Apprise 通知发送历史'}

    # 无默认值字段须排在带默认值字段之前（SQLAlchemy dataclass）
    id: Mapped[id_key] = mapped_column(init=False)
    status: Mapped[str] = mapped_column(sa.String(32), comment='success 或 failed')
    channel_id: Mapped[int | None] = mapped_column(
        sa.BigInteger,
        nullable=True,
        index=True,
        default=None,
        comment='通道 ID',
    )
    channel_name: Mapped[str] = mapped_column(sa.String(128), default='', comment='发送时通道名快照')
    title: Mapped[str] = mapped_column(sa.String(255), default='', comment='标题')
    body: Mapped[str] = mapped_column(UniversalText, default='', comment='正文')
    error_message: Mapped[str | None] = mapped_column(UniversalText, default=None, comment='失败原因')
    trigger_source: Mapped[str] = mapped_column(
        sa.String(32),
        default='',
        comment='触发来源：test=通道测试 notify=通知接口',
    )
