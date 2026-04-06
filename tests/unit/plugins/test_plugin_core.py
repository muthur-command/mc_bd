"""backend.plugin.core — 插件发现与配置加载（不启动 Redis）。"""

from backend.plugin.core import get_plugins, load_plugin_config


def test_get_plugins_includes_known_packages() -> None:
    names = get_plugins()
    assert 'apprise_notify' in names
    assert 'oauth2' in names
    assert all('.backup' not in n for n in names)


def test_load_plugin_config_returns_nested_dict() -> None:
    data = load_plugin_config('card')
    assert 'plugin' in data
    assert 'app' in data
