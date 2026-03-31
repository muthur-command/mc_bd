"""Docker配置模型"""
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key


class DockerConfig(Base):
    """Docker配置表"""

    __tablename__ = 'docker_config'
    __table_args__ = {'comment': 'Docker配置表'}

    id: Mapped[id_key] = mapped_column(init=False)
    key: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True, comment='配置键')
    value: Mapped[str] = mapped_column(sa.Text, comment='配置值')

