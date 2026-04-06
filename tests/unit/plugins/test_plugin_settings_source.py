"""backend.plugin.settings_source — 从插件目录合并 settings。"""

from unittest.mock import patch

from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.plugin.settings_source import PluginSettingsSource


class _MiniSettings(BaseSettings):
    model_config = SettingsConfigDict(extra='allow')


def test_plugin_settings_source_merges_plugin_toml_settings(tmp_path) -> None:
    plug = tmp_path / 'demo_plug'
    plug.mkdir()
    (plug / '__init__.py').write_text('', encoding='utf-8')
    (plug / 'plugin.toml').write_text(
        '[plugin]\nsummary = "x"\nversion = "1.0.0"\ndescription = "dddddddddd"\nauthor = "a"\n\n[settings]\nONLY_FROM_PLUGIN = "merged"\n',
        encoding='utf-8',
    )

    with patch('backend.plugin.settings_source.PLUGIN_DIR', tmp_path):
        src = PluginSettingsSource(_MiniSettings)
        data = src()

    assert data.get('ONLY_FROM_PLUGIN') == 'merged'
