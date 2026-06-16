"""首次启动时灌入 mc_init_default_data.sql 中的默认角色与用户。"""

from pathlib import Path

from sqlalchemy import text

from backend.common.enums import DataBaseType
from backend.common.log import log
from backend.core.conf import settings
from backend.core.path_conf import MYSQL_SCRIPT_DIR, POSTGRESQL_SCRIPT_DIR
from backend.database.db import async_engine
from backend.utils.sql_parser import parse_sql_script

DEFAULT_DATA_SQL_FILENAME = 'mc_init_default_data.sql'


def get_default_data_sql_path() -> Path:
    """返回当前数据库类型对应的默认数据 SQL 路径。"""
    script_dir = MYSQL_SCRIPT_DIR if DataBaseType.mysql == settings.DATABASE_TYPE else POSTGRESQL_SCRIPT_DIR
    return script_dir / DEFAULT_DATA_SQL_FILENAME


async def is_database_seeded() -> bool:
    """若 sys_user 已有记录则视为已灌入默认数据。"""
    async with async_engine.connect() as conn:
        result = await conn.execute(text('SELECT 1 FROM sys_user LIMIT 1'))
        return result.scalar() is not None


async def execute_sql_file(filepath: Path | str) -> None:
    """按语句顺序执行 SQL 脚本文件。"""
    async with async_engine.begin() as conn:
        for stmt in await parse_sql_script(str(filepath)):
            await conn.execute(text(stmt))


async def seed_default_data_if_empty() -> None:
    """首次启动时执行 mc_init_default_data.sql（已有用户则跳过）。"""
    sql_path = get_default_data_sql_path()
    if not sql_path.is_file():
        log.warning('默认数据 SQL 文件不存在，跳过：{}', sql_path)
        return

    if await is_database_seeded():
        log.debug('数据库已有用户，跳过默认数据初始化')
        return

    log.info('首次启动：正在灌入默认数据（{}）', sql_path.name)
    await execute_sql_file(sql_path)
    log.info('默认数据初始化完成')
