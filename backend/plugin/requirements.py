import importlib.util
import os
import shutil
import subprocess
import sys

from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

from packaging.requirements import Requirement
from starlette.concurrency import run_in_threadpool

from backend.core.conf import settings
from backend.core.path_conf import PLUGIN_DIR
from backend.plugin.errors import PluginInstallError


def get_plugins() -> list[str]:
    """
    获取插件列表

    注意：此函数从 backend.plugin.core 导入以避免循环依赖
    """
    from backend.plugin.core import get_plugins as _get_plugins

    return _get_plugins()


def _is_in_virtualenv() -> bool:
    """检测当前是否在虚拟环境中运行"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def _resolve_uv_executable() -> str | None:
    """
    解析 uv 可执行文件路径。

    uv 管理的 .venv 里往往没有 pip，`python -m pip` 会失败；应优先调用 uv。
    PATH 中可能没有 uv（如 sudo root），再尝试常见安装位置。
    """
    found = shutil.which('uv')
    if found:
        return found
    home = Path.home()
    for candidate in (
        home / '.local' / 'bin' / 'uv',
        home / '.cargo' / 'bin' / 'uv',
    ):
        resolved = _candidate_uv_if_executable(candidate)
        if resolved:
            return resolved
    return None


def _candidate_uv_if_executable(candidate: Path) -> str | None:
    try:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    except OSError:
        pass
    return None


def _has_pip_module() -> bool:
    return importlib.util.find_spec('pip') is not None


def _requirement_is_installed(req: Requirement) -> bool:
    """Return True when a requirements.txt line is already satisfied."""
    for candidate in {req.name, req.name.replace('-', '_'), req.name.replace('_', '-')}:
        try:
            dist = distribution(candidate)
        except PackageNotFoundError:
            continue
        if not req.specifier:
            return True
        if req.specifier.contains(dist.version, prereleases=True):
            return True

    module_name = req.name.replace('-', '_')
    return importlib.util.find_spec(module_name) is not None


def _missing_requirements(requirements_file: Path) -> list[str]:
    missing: list[str] = []
    with requirements_file.open(encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                req = Requirement(line)
            except Exception as e:
                raise PluginInstallError(f'插件依赖 {line} 格式错误: {e!s}') from e
            if not _requirement_is_installed(req):
                missing.append(line)
    return missing


def _plugin_pip_install_cmd(requirements_file: str) -> list[str]:
    """
    构造安装插件依赖的命令。

    优先 uv；否则使用当前解释器的 pip（仅当 venv 内已安装 pip 模块）。
    """
    req = str(requirements_file)
    uv_bin = _resolve_uv_executable()
    if uv_bin:
        cmd = [uv_bin, 'pip', 'install', '-r', req]
        if not _is_in_virtualenv():
            cmd.append('--system')
    elif _has_pip_module():
        cmd = [sys.executable, '-m', 'pip', 'install', '-r', req]
    else:
        raise PluginInstallError(
            '无法安装插件依赖：当前环境无 uv，且未安装 pip 模块。'
            '请在本项目目录执行 `uv sync`，或将插件依赖写入 pyproject.toml 后重新同步。',
        )
    if settings.PLUGIN_PIP_CHINA:
        cmd.extend(['-i', settings.PLUGIN_PIP_INDEX_URL])
    return cmd


def _plugin_pip_uninstall_cmd(requirements_file: str) -> list[str]:
    req = str(requirements_file)
    uv_bin = _resolve_uv_executable()
    if uv_bin:
        cmd = [uv_bin, 'pip', 'uninstall', '-r', req, '-y']
        if not _is_in_virtualenv():
            cmd.append('--system')
    elif _has_pip_module():
        cmd = [sys.executable, '-m', 'pip', 'uninstall', '-r', req, '-y']
    else:
        raise PluginInstallError(
            '无法卸载插件依赖：当前环境无 uv 且无 pip。请使用 `uv pip uninstall -r ...` 手动处理。',
        )
    return cmd


def install_requirements(plugin: str | None) -> None:
    """
    安装插件依赖

    :param plugin: 指定插件名，否则检查所有插件
    :return:
    """
    plugins = [plugin] if plugin else get_plugins()

    for plugin in plugins:
        requirements_file = PLUGIN_DIR / plugin / 'requirements.txt'
        if not requirements_file.is_file():
            continue

        missing = _missing_requirements(requirements_file)
        if not missing:
            continue

        if settings.ENVIRONMENT == 'prod':
            raise PluginInstallError(
                f'插件 {plugin} 缺少预装依赖：{", ".join(missing)}。'
                '生产镜像应在构建阶段通过 pyproject.toml / uv sync 安装全部依赖，'
                '容器启动时不应访问 PyPI。请更新 mc_bd 镜像后重试。',
            )

        pip_install = _plugin_pip_install_cmd(str(requirements_file))

        max_retries = settings.PLUGIN_PIP_MAX_RETRY
        for attempt in range(max_retries):
            try:
                subprocess.check_call(
                    pip_install,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                break
            except subprocess.TimeoutExpired:
                if attempt == max_retries - 1:
                    raise PluginInstallError(f'插件 {plugin} 依赖安装超时')
                continue
            except subprocess.CalledProcessError as e:
                if attempt == max_retries - 1:
                    raise PluginInstallError(f'插件 {plugin} 依赖安装失败：{e}') from e
                continue


def uninstall_requirements(plugin: str) -> None:
    """
    卸载插件依赖

    :param plugin: 插件名称
    :return:
    """
    requirements_file = PLUGIN_DIR / plugin / 'requirements.txt'
    if os.path.exists(requirements_file):
        try:
            pip_uninstall = _plugin_pip_uninstall_cmd(requirements_file)
            subprocess.check_call(pip_uninstall, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            raise PluginInstallError(f'插件 {plugin} 依赖卸载失败：{e}') from e


async def install_requirements_async(plugin: str | None = None) -> None:
    """
    异步安装插件依赖

    由于 Windows 平台限制，无法实现完美的全异步方案，详情：
    https://stackoverflow.com/questions/44633458/why-am-i-getting-notimplementederror-with-async-and-await-on-windows
    """
    await run_in_threadpool(install_requirements, plugin)


async def uninstall_requirements_async(plugin: str) -> None:
    """
    异步卸载插件依赖

    :param plugin: 插件名称
    :return:
    """
    await run_in_threadpool(uninstall_requirements, plugin)
