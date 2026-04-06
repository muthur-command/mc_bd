"""Bento 布局表：存储每页的网格布局 JSON"""

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, UniversalText, id_key


class BentoLayoutRecord(Base):
    """Bento 布局持久化表"""

    __tablename__ = 'plugin_bento_layout'
    __table_args__ = {'comment': 'Bento 布局表'}

    id: Mapped[id_key] = mapped_column(init=False)
    page_id: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True, comment='页面 ID')
    layout_data: Mapped[str] = mapped_column(UniversalText, comment='布局 JSON')
