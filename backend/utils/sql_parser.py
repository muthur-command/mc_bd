import anyio

from anyio import open_file
from sqlparse import split

from backend.common.exception import errors


def _strip_leading_comments(stmt: str) -> str:
    """去掉语句前导的空白行和 -- 注释行，便于校验首词"""
    lines = stmt.splitlines()
    start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s and not s.startswith('--'):
            start = i
            break
    return '\n'.join(lines[start:]).strip()


async def parse_sql_script(filepath: str) -> list[str]:
    """
    解析 SQL 脚本

    :param filepath: 脚本文件路径
    :return:
    """
    path = anyio.Path(filepath)
    if not await path.exists():
        raise errors.NotFoundError(msg='SQL 脚本文件不存在')

    async with await open_file(filepath, encoding='utf-8') as f:
        contents = await f.read(1024)
        while additional_contents := await f.read(1024):
            contents += additional_contents

    statements = split(contents)
    allowed_starts = ('select', 'insert', 'create', 'drop', 'alter', 'comment')
    result = []
    for statement in statements:
        stmt_stripped = statement.strip()
        if not stmt_stripped:
            continue
        # 去掉前导注释后再校验，避免 "-- 注释\nCREATE TABLE ..." 被拒
        to_check = _strip_leading_comments(stmt_stripped)
        if not to_check:
            continue
        if not any(to_check.lower().startswith(_) for _ in allowed_starts):
            raise errors.RequestError(msg='SQL 脚本文件中存在非法操作，仅允许 SELECT、INSERT、CREATE、DROP、ALTER')
        result.append(statement)
    return result
