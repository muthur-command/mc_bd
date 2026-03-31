import sqlalchemy as sa

from backend.common.model import MappedBase

# 用户角色表
user_role = sa.Table(
    'sys_user_role',
    MappedBase.metadata,
    sa.Column('id', sa.BigInteger, primary_key=True, unique=True, index=True, autoincrement=True, comment='主键ID'),
    sa.Column('user_id', sa.BigInteger, primary_key=True, comment='用户ID'),
    sa.Column('role_id', sa.BigInteger, primary_key=True, comment='角色ID'),
)
