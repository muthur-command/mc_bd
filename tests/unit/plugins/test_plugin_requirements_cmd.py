"""backend.plugin.requirements — 依赖安装命令构造（不执行 subprocess）。"""

from unittest.mock import patch

import pytest

from backend.core.conf import settings
from backend.plugin.errors import PluginInstallError
from backend.plugin.requirements import _plugin_pip_install_cmd, _plugin_pip_uninstall_cmd


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
