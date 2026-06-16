"""backend.utils.sql_parser"""

import pytest

from backend.common.exception import errors
from backend.utils.sql_parser import parse_sql_script


@pytest.mark.asyncio
async def test_parse_sql_script_create_table(tmp_path) -> None:
    p = tmp_path / 'init.sql'
    p.write_text('-- header\nCREATE TABLE t (id INT);\n', encoding='utf-8')
    stmts = await parse_sql_script(str(p))
    assert any('CREATE TABLE' in s.upper() for s in stmts)


@pytest.mark.asyncio
async def test_parse_sql_script_comment_on_table(tmp_path) -> None:
    p = tmp_path / 'comment.sql'
    p.write_text("COMMENT ON TABLE sys_role IS '角色表';\n", encoding='utf-8')
    stmts = await parse_sql_script(str(p))
    assert len(stmts) == 1
    assert 'COMMENT ON TABLE' in stmts[0].upper()


@pytest.mark.asyncio
async def test_parse_sql_script_mc_init_default_data() -> None:
    from backend.core.path_conf import POSTGRESQL_SCRIPT_DIR

    stmts = await parse_sql_script(str(POSTGRESQL_SCRIPT_DIR / 'mc_init_default_data.sql'))
    assert any('COMMENT ON TABLE' in s.upper() for s in stmts)
    assert any('CREATE TABLE' in s.upper() for s in stmts)


@pytest.mark.asyncio
async def test_parse_sql_script_rejects_disallowed(tmp_path) -> None:
    p = tmp_path / 'bad.sql'
    p.write_text('DELETE FROM t;\n', encoding='utf-8')
    with pytest.raises(errors.RequestError):
        await parse_sql_script(str(p))


@pytest.mark.asyncio
async def test_parse_sql_script_missing_file() -> None:
    with pytest.raises(errors.NotFoundError):
        await parse_sql_script('/nonexistent/mc_bd_test.sql')
