"""插件内测试：由根目录 pytest 与 backend/plugin 一并收集。"""

from pathlib import Path

from backend.plugin.core import load_plugin_config
from backend.plugin.validator import validate_plugin_config


def test_plugin_toml_passes_validation() -> None:
    plugin = Path(__file__).resolve().parents[1].name
    data = load_plugin_config(plugin)
    validate_plugin_config(plugin, data)
