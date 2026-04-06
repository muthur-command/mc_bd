"""backend.plugin.validator — Pydantic 插件配置模型。"""

import pytest

from backend.common.enums import PluginLevelType
from backend.plugin.errors import PluginConfigError
from backend.plugin.validator import (
    ApiConfigSchema,
    AppPluginConfigSchema,
    PluginInfoSchema,
    validate_plugin_config,
)


def test_plugin_info_schema_valid() -> None:
    m = PluginInfoSchema(
        summary="s",
        version="1.0.0",
        description="d" * 10,
        author="a",
        tags=["internal"],
        database=["postgresql"],
    )
    assert m.version == "1.0.0"


def test_plugin_info_schema_version_invalid() -> None:
    with pytest.raises(PluginConfigError):
        PluginInfoSchema(
            summary="s",
            version="v1",
            description="d" * 10,
            author="a",
        )


def test_api_config_prefix_must_start_with_slash() -> None:
    with pytest.raises(PluginConfigError):
        ApiConfigSchema(prefix="api", tags="t")


def test_validate_app_level_plugin() -> None:
    cfg = {
        "plugin": {
            "summary": "x",
            "version": "0.0.1",
            "description": "y" * 5,
            "author": "z",
            "tags": ["notification"],
            "database": ["mysql"],
        },
        "app": {"router": ["v1"]},
        "settings": {},
    }
    level = validate_plugin_config("fake", cfg)
    assert level == PluginLevelType.app


def test_validate_extend_level_plugin() -> None:
    cfg = {
        "plugin": {
            "summary": "x",
            "version": "1.0.0",
            "description": "y" * 5,
            "author": "z",
            "tags": ["internal"],
            "database": ["mysql"],
        },
        "app": {"extend": "admin"},
        "api": {"v1": {"prefix": "/demo", "tags": "Demo"}},
        "settings": {},
    }
    level = validate_plugin_config("fake_extend", cfg)
    assert level == PluginLevelType.extend


def test_app_plugin_config_schema_rejects_lowercase_settings_key() -> None:
    cfg = {
        "plugin": {
            "summary": "x",
            "version": "0.0.1",
            "description": "y" * 5,
            "author": "z",
        },
        "app": {"router": ["v1"]},
        "settings": {"bad": 1},
    }
    with pytest.raises(PluginConfigError):
        AppPluginConfigSchema.model_validate(cfg)
