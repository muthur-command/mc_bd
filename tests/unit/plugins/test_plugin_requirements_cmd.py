"""backend.plugin.requirements — 依赖安装命令构造（不执行 subprocess）。"""

from unittest.mock import patch

import pytest

from packaging.requirements import Requirement

from backend.core.conf import settings
from backend.plugin.errors import PluginInstallError
from backend.plugin.requirements import (
    _plugin_pip_install_cmd,
    _plugin_pip_uninstall_cmd,
    _requirement_is_installed,
    install_requirements,
)


def test_plugin_pip_install_cmd_prefers_uv() -> None:
    with (
        patch('backend.plugin.requirements._resolve_uv_executable', return_value='/fake/uv'),
        patch.object(settings, 'PLUGIN_PIP_CHINA', False),
    ):
        cmd = _plugin_pip_install_cmd('/tmp/req.txt')
    assert cmd[:4] == ['/fake/uv', 'pip', 'install', '-r']
    assert str(cmd[4]) == '/tmp/req.txt'


def test_plugin_pip_install_cmd_appends_index_when_china_mirror() -> None:
    with (
        patch('backend.plugin.requirements._resolve_uv_executable', return_value='/uv'),
        patch.object(settings, 'PLUGIN_PIP_CHINA', True),
        patch.object(settings, 'PLUGIN_PIP_INDEX_URL', 'https://pypi.example/simple'),
    ):
        cmd = _plugin_pip_install_cmd('/r.txt')
    assert '-i' in cmd
    assert 'https://pypi.example/simple' in cmd


def test_plugin_pip_install_cmd_raises_without_uv_or_pip() -> None:
    with (
        patch('backend.plugin.requirements._resolve_uv_executable', return_value=None),
        patch('backend.plugin.requirements._has_pip_module', return_value=False),
    ):
        with pytest.raises(PluginInstallError, match='无法安装插件依赖'):
            _plugin_pip_install_cmd('/x.txt')


def test_plugin_pip_uninstall_cmd_uses_uv() -> None:
    with patch('backend.plugin.requirements._resolve_uv_executable', return_value='/uv'):
        cmd = _plugin_pip_uninstall_cmd('/r.txt')
    assert cmd[:4] == ['/uv', 'pip', 'uninstall', '-r']


def test_requirement_is_installed_python_on_whales() -> None:
    assert _requirement_is_installed(Requirement('python-on-whales')) is True


def test_install_requirements_prod_skips_runtime_pip(tmp_path) -> None:
    plugin_dir = tmp_path / 'demo'
    plugin_dir.mkdir()
    (plugin_dir / 'requirements.txt').write_text('missing-plugin-xyz\n', encoding='utf-8')

    with (
        patch('backend.plugin.requirements.PLUGIN_DIR', tmp_path),
        patch('backend.plugin.requirements.get_plugins', return_value=['demo']),
        patch.object(settings, 'ENVIRONMENT', 'prod'),
        patch('backend.plugin.requirements.subprocess.check_call') as mock_install,
    ):
        with pytest.raises(PluginInstallError, match='缺少预装依赖'):
            install_requirements('demo')
    mock_install.assert_not_called()
