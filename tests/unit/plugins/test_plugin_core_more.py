"""backend.plugin.core — SQL 路径、配置缺失、模型列表、状态校验、应用级路由注入。"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import APIRouter

from backend.common.enums import DataBaseType, PrimaryKeyType, StatusType
from backend.common.exception import errors
from backend.plugin.core import (
    _plugin_status_checker_impl,
    get_plugin_models,
    get_plugin_sql,
    get_plugin_status_checker,
    inject_app_router,
    load_plugin_config,
)
from backend.plugin.errors import PluginInjectError


@pytest.mark.asyncio
async def test_get_plugin_sql_mysql_autoincrement_returns_path(tmp_path) -> None:
    plugin = "p1"
    sql_file = tmp_path / plugin / "sql" / "mysql" / "init.sql"
    sql_file.parent.mkdir(parents=True)
    sql_file.write_text("-- x", encoding="utf-8")
    with patch("backend.plugin.core.PLUGIN_DIR", tmp_path):
        out = await get_plugin_sql(plugin, DataBaseType.mysql, PrimaryKeyType.autoincrement)
    assert out == sql_file


@pytest.mark.asyncio
async def test_get_plugin_sql_mysql_snowflake_file(tmp_path) -> None:
    plugin = "p1"
    sql_file = tmp_path / plugin / "sql" / "mysql" / "init_snowflake.sql"
    sql_file.parent.mkdir(parents=True)
    sql_file.write_text("-- y", encoding="utf-8")
    with patch("backend.plugin.core.PLUGIN_DIR", tmp_path):
        out = await get_plugin_sql(plugin, DataBaseType.mysql, PrimaryKeyType.snowflake)
    assert out == sql_file


@pytest.mark.asyncio
async def test_get_plugin_sql_missing_returns_none(tmp_path) -> None:
    with patch("backend.plugin.core.PLUGIN_DIR", tmp_path):
        out = await get_plugin_sql("nop", DataBaseType.postgresql, PrimaryKeyType.autoincrement)
    assert out is None


def test_load_plugin_config_missing_toml_raises(tmp_path) -> None:
    with patch("backend.plugin.core.PLUGIN_DIR", tmp_path):
        with pytest.raises(PluginInjectError, match="缺少 plugin.toml"):
            load_plugin_config("ghost")


def test_get_plugin_models_empty_when_no_plugins() -> None:
    with patch("backend.plugin.core.get_plugins", return_value=[]):
        assert get_plugin_models() == []


@pytest.mark.asyncio
async def test_plugin_status_checker_impl_no_redis_raises() -> None:
    with patch("backend.plugin.core.redis_client") as rc:
        rc.get = AsyncMock(return_value=None)
        with pytest.raises(PluginInjectError, match="未初始化"):
            await _plugin_status_checker_impl("card")


@pytest.mark.asyncio
async def test_plugin_status_checker_impl_disabled_raises_server_error() -> None:
    payload = json.dumps({"plugin": {"enable": str(StatusType.disable.value)}})
    with patch("backend.plugin.core.redis_client") as rc:
        rc.get = AsyncMock(return_value=payload)
        with pytest.raises(errors.ServerError) as ei:
            await _plugin_status_checker_impl("card")
        assert "未启用" in (ei.value.msg or "")


@pytest.mark.asyncio
async def test_plugin_status_checker_impl_enabled_noop() -> None:
    payload = json.dumps({"plugin": {"enable": str(StatusType.enable.value)}})
    with patch("backend.plugin.core.redis_client") as rc:
        rc.get = AsyncMock(return_value=payload)
        await _plugin_status_checker_impl("card")
    rc.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_plugin_status_checker_delegates() -> None:
    payload = json.dumps({"plugin": {"enable": str(StatusType.enable.value)}})
    with patch("backend.plugin.core.redis_client") as rc:
        rc.get = AsyncMock(return_value=payload)
        check = get_plugin_status_checker("card")
        await check()
    rc.get.assert_awaited_once()


def test_inject_app_router_include_routers() -> None:
    sub = APIRouter()

    @sub.get("/plugin-x")
    async def _probe() -> dict:
        return {"ok": True}

    plugin = {"plugin": {"name": "fakeplug"}, "app": {"router": ["router_a"]}}
    mod = SimpleNamespace(router_a=sub)
    target = APIRouter()
    with patch("backend.plugin.core.import_module_cached", return_value=mod):
        inject_app_router(plugin, target)

    paths = {getattr(r, "path", None) for r in target.routes}
    assert "/plugin-x" in paths
