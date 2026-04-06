"""backend.cli — CustomReloadFilter、execute_sql_scripts、get_sql_scripts、install_plugin 守卫。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from watchfiles import Change

from backend.cli import CustomReloadFilter, execute_sql_scripts, get_sql_scripts, install_plugin
from backend.common.enums import DataBaseType, PrimaryKeyType


def test_custom_reload_filter_false_when_lock_file_exists() -> None:
    flt = CustomReloadFilter()
    with patch("backend.cli.RELOAD_LOCK_FILE") as p:
        p.exists.return_value = True
        assert flt(Change.added, "/tmp/x.py") is False


def test_custom_reload_filter_delegates_when_no_lock(tmp_path) -> None:
    flt = CustomReloadFilter()
    py = tmp_path / "m.py"
    py.write_text("x=1\n", encoding="utf-8")
    with patch("backend.cli.RELOAD_LOCK_FILE") as p:
        p.exists.return_value = False
        out = flt(Change.added, str(py))
    assert isinstance(out, bool)


@pytest.mark.asyncio
async def test_execute_sql_scripts_runs_statements() -> None:
    db = MagicMock()
    db.execute = AsyncMock()
    with patch("backend.cli.parse_sql_script", new_callable=AsyncMock, return_value=["SELECT 1", "SELECT 2"]):
        await execute_sql_scripts(db, "any.sql", is_init=True)
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_execute_sql_scripts_wraps_failure_as_exit() -> None:
    db = MagicMock()
    db.execute = AsyncMock()
    with patch("backend.cli.parse_sql_script", new_callable=AsyncMock, side_effect=RuntimeError("boom")):
        import cappa

        with pytest.raises(cappa.Exit) as ei:
            await execute_sql_scripts(db, "bad.sql")
        assert ei.value.code == 1


@pytest.mark.asyncio
async def test_get_sql_scripts_includes_main_and_plugin_sql(tmp_path) -> None:
    """主 init SQL 存在时加入列表；每个插件返回的路径非空则追加。"""
    import backend.cli as cli_mod

    sql_dir = tmp_path / "pg"
    sql_dir.mkdir()
    init_file = sql_dir / "init_test_data.sql"
    init_file.write_text("-- empty", encoding="utf-8")

    fake_ap = MagicMock()
    fake_ap.exists = AsyncMock(return_value=True)

    with (
        patch.object(cli_mod, "POSTGRESQL_SCRIPT_DIR", sql_dir),
        patch.object(cli_mod, "MYSQL_SCRIPT_DIR", sql_dir),
        patch.object(cli_mod.settings, "DATABASE_TYPE", DataBaseType.postgresql),
        patch.object(cli_mod.settings, "DATABASE_PK_MODE", PrimaryKeyType.autoincrement),
        patch.object(cli_mod.anyio, "Path", return_value=fake_ap),
        patch.object(cli_mod, "get_plugins", return_value=["email"]),
        patch.object(
            cli_mod,
            "get_plugin_sql",
            new_callable=AsyncMock,
            return_value="/only/plugin.sql",
        ),
    ):
        scripts = await get_sql_scripts()

    assert str(init_file) in scripts
    assert "/only/plugin.sql" in scripts


@pytest.mark.asyncio
async def test_install_plugin_requires_dev_environment() -> None:
    import backend.cli as cli_mod
    import cappa

    with patch.object(cli_mod.settings, "ENVIRONMENT", "prod"):
        with pytest.raises(cappa.Exit) as ei:
            await install_plugin("/x.zip", None, False, DataBaseType.postgresql, PrimaryKeyType.autoincrement)
        assert ei.value.code == 1


@pytest.mark.asyncio
async def test_install_plugin_requires_path_or_repo() -> None:
    import backend.cli as cli_mod
    import cappa

    with patch.object(cli_mod.settings, "ENVIRONMENT", "dev"):
        with pytest.raises(cappa.Exit) as ei:
            await install_plugin("", None, False, DataBaseType.postgresql, PrimaryKeyType.autoincrement)
        assert ei.value.code == 1
