import sys

from collections.abc import AsyncGenerator
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.common.enums import DataBaseType
from backend.common.log import log
from backend.common.model import MappedBase
from backend.core.conf import settings

# Gunicorn 多 worker 并发 lifespan 时串行建表，避免 duplicate sequence 错误。
CREATE_TABLES_LOCK_KEY = 'mc:schema:create_tables'
CREATE_TABLES_LOCK_TIMEOUT = 300
CREATE_TABLES_LOCK_BLOCKING_TIMEOUT = 120


def create_database_url(*, unittest: bool = False, with_database: bool = True) -> URL:
    """
    创建数据库链接

    :param unittest: 是否用于单元测试
    :param with_database: 是否包含数据库名（创建数据库时不需要）
    :return:
    """
    if with_database:
        database = settings.DATABASE_SCHEMA if not unittest else f'{settings.DATABASE_SCHEMA}_test'
    else:
        database = None if DataBaseType.mysql == settings.DATABASE_TYPE else 'postgres'

    url = URL.create(
        drivername='mysql+asyncmy' if DataBaseType.mysql == settings.DATABASE_TYPE else 'postgresql+asyncpg',
        username=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=database,
    )
    if DataBaseType.mysql == settings.DATABASE_TYPE and with_database:
        url = url.update_query_dict({'charset': settings.DATABASE_CHARSET})
    return url


def create_database_async_engine(url: str | URL) -> AsyncEngine:
    """
    创建数据库异步引擎

    :param url: 数据库连接地址
    :return:
    """
    try:
        return create_async_engine(
            url,
            echo=settings.DATABASE_ECHO,
            echo_pool=settings.DATABASE_POOL_ECHO,
            future=True,
            # 中等并发
            pool_size=10,  # 低：- 高：+
            max_overflow=20,  # 低：- 高：+
            pool_timeout=30,  # 低：+ 高：-
            pool_recycle=3600,  # 低：+ 高：-
            pool_pre_ping=True,  # 低：False 高：True
            pool_use_lifo=False,  # 低：False 高：True
        )
    except Exception as e:
        log.error(f'数据库连接失败 {e}')
        sys.exit()


def create_database_async_session(engine: AsyncEngine) -> async_sessionmaker[AsyncSession | Any]:
    """
    创建数据库异步会话

    :param engine: 数据库异步引擎
    :return:
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,  # 禁用自动刷新
        expire_on_commit=False,  # 禁用提交时过期
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with async_db_session() as session:
        yield session


async def get_db_transaction() -> AsyncGenerator[AsyncSession, None]:
    """获取带有事务的数据库会话"""
    async with async_db_session.begin() as session:
        yield session


async def create_tables() -> None:
    """创建数据库表并在首次启动时灌入默认数据。

    Redis 分布式锁保证多 worker 下 DDL 与 seed 只执行一次。
    """
    from backend.database.redis import redis_client
    from backend.database.seed import seed_default_data_if_empty

    try:
        async with redis_client.lock(
            CREATE_TABLES_LOCK_KEY,
            timeout=CREATE_TABLES_LOCK_TIMEOUT,
            blocking_timeout=CREATE_TABLES_LOCK_BLOCKING_TIMEOUT,
        ):
            async with async_engine.begin() as coon:
                await coon.run_sync(MappedBase.metadata.create_all)
            await seed_default_data_if_empty()
    except Exception as e:
        log.error('创建数据库表失败 {}', e)
        sys.exit()


async def drop_tables() -> None:
    """丢弃数据库表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(MappedBase.metadata.drop_all)


def uuid4_str() -> str:
    """数据库引擎 UUID 类型兼容性解决方案"""
    return str(uuid4())


# SQLA 数据库链接
SQLALCHEMY_DATABASE_URL = create_database_url()

# SALA 异步引擎和会话
async_engine = create_database_async_engine(SQLALCHEMY_DATABASE_URL)
async_db_session = create_database_async_session(async_engine)

# Session Annotated
CurrentSession = Annotated[AsyncSession, Depends(get_db)]
CurrentSessionTransaction = Annotated[AsyncSession, Depends(get_db_transaction)]
