"""mc_init_default_data.sql 中的测试密码须与注释一致（123456）。"""

import re

from pathlib import Path

import pytest

from backend.app.admin.utils.password_security import password_verify
from backend.core.path_conf import MYSQL_SCRIPT_DIR, POSTGRESQL_SCRIPT_DIR

SEED_PASSWORD = '123456'
_HASH_PATTERN = re.compile(r"'(\$2b\$[^']+)'")


def _extract_first_bcrypt_hash(sql_text: str) -> str:
    match = _HASH_PATTERN.search(sql_text)
    assert match is not None, 'seed SQL 中未找到 bcrypt 密码哈希'
    return match.group(1)


@pytest.mark.parametrize(
    'sql_path',
    [
        POSTGRESQL_SCRIPT_DIR / 'mc_init_default_data.sql',
        MYSQL_SCRIPT_DIR / 'mc_init_default_data.sql',
    ],
)
def test_seed_sql_default_password_matches_comment(sql_path: Path) -> None:
    text = sql_path.read_text(encoding='utf-8')
    password_hash = _extract_first_bcrypt_hash(text)
    assert password_verify(SEED_PASSWORD, password_hash), (
        f'{sql_path.name} 中的 bcrypt 哈希与默认密码 {SEED_PASSWORD!r} 不匹配'
    )
