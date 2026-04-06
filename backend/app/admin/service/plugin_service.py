import io
import json
import os
import shutil
import zipfile

from typing import Any

import anyio
import httpx

from fastapi import UploadFile

from backend.common.enums import PluginType, StatusType
from backend.common.exception import errors
from backend.core.conf import settings
from backend.core.path_conf import PLUGIN_DIR
from backend.database.redis import redis_client
from backend.plugin.installer import install_git_plugin, install_zip_plugin
from backend.plugin.requirements import uninstall_requirements_async
from backend.utils.timezone import timezone

REMOTE_LIST_URL_KEY = f'{settings.PLUGIN_REDIS_PREFIX}:remote_list_url'
REMOTE_LIST_URLS_KEY = f'{settings.PLUGIN_REDIS_PREFIX}:remote_list_urls'


class PluginService:
    """插件服务类"""

    @staticmethod
    async def get_all() -> list[dict[str, Any]]:
        """获取所有插件"""
        changed_key = f'{settings.PLUGIN_REDIS_PREFIX}:changed'
        keys = [key async for key in redis_client.scan_iter(f'{settings.PLUGIN_REDIS_PREFIX}:*') if key != changed_key]
        if not keys:
            return []
        values = await redis_client.mget(*keys)
        result = []
        for info in values:
            if not info:
                continue
            try:
                result.append(json.loads(info))
            except (json.JSONDecodeError, TypeError):
                continue
        return result

    @staticmethod
    async def changed() -> str | None:
        """检查插件是否发生变更"""
        return await redis_client.get(f'{settings.PLUGIN_REDIS_PREFIX}:changed')

    @staticmethod
    async def install(*, type: PluginType, file: UploadFile | None = None, repo_url: str | None = None) -> str:
        """
        安装插件

        :param type: 插件类型
        :param file: 插件 zip 压缩包
        :param repo_url: git 仓库地址
        :return:
        """
        if settings.ENVIRONMENT != 'dev':
            raise errors.RequestError(msg='error.plugin_install_dev_only')
        if type == PluginType.zip:
            if not file:
                raise errors.RequestError(msg='error.plugin_zip_empty')
            return await install_zip_plugin(file)
        if not repo_url:
            raise errors.RequestError(msg='error.plugin_git_url_required')
        return await install_git_plugin(repo_url)

    @staticmethod
    async def uninstall(*, plugin: str) -> None:
        """
        卸载插件

        :param plugin: 插件名称
        :return:
        """
        if settings.ENVIRONMENT != 'dev':
            raise errors.RequestError(msg='error.plugin_uninstall_dev_only')
        plugin_dir = anyio.Path(PLUGIN_DIR / plugin)
        if not await plugin_dir.exists():
            raise errors.NotFoundError(msg='error.plugin_not_found')
        await uninstall_requirements_async(plugin)
        bacup_dir = PLUGIN_DIR / f'{plugin}.{timezone.now().strftime("%Y%m%d%H%M%S")}.backup'
        shutil.move(plugin_dir, bacup_dir)
        await redis_client.delete(f'{settings.PLUGIN_REDIS_PREFIX}:{plugin}')
        await redis_client.set(f'{settings.PLUGIN_REDIS_PREFIX}:changed', 'ture')

    @staticmethod
    async def update_status(*, plugin: str) -> None:
        """
        更新插件状态

        :param plugin: 插件名称
        :return:
        """
        plugin_info = await redis_client.get(f'{settings.PLUGIN_REDIS_PREFIX}:{plugin}')
        if not plugin_info:
            raise errors.NotFoundError(msg='error.plugin_not_found')
        plugin_info = json.loads(plugin_info)

        # 更新持久缓存状态
        new_status = (
            str(StatusType.enable.value)
            if plugin_info['plugin']['enable'] == str(StatusType.disable.value)
            else str(StatusType.disable.value)
        )
        plugin_info['plugin']['enable'] = new_status
        await redis_client.set(f'{settings.PLUGIN_REDIS_PREFIX}:{plugin}', json.dumps(plugin_info, ensure_ascii=False))

    @staticmethod
    async def get_remote_list_url() -> str | None:
        """获取远程插件列表 JSON 地址（兼容旧单 URL）"""
        return await redis_client.get(REMOTE_LIST_URL_KEY)

    @staticmethod
    async def get_remote_list_urls() -> list[str]:
        """获取远程插件列表 JSON 地址列表（多 URL）"""
        raw = await redis_client.get(REMOTE_LIST_URLS_KEY)
        if not raw:
            single = await redis_client.get(REMOTE_LIST_URL_KEY)
            if single and single.strip():
                return [single.strip()]
            return []
        try:
            urls = json.loads(raw)
            return [u for u in urls if isinstance(u, str) and u.strip()]
        except (json.JSONDecodeError, TypeError):
            return []

    @staticmethod
    async def set_remote_list_url(url: str) -> None:
        """设置远程插件列表 JSON 地址（兼容旧接口，写入单 URL 并同步到 url 列表）"""
        await redis_client.set(REMOTE_LIST_URL_KEY, url.strip())
        await redis_client.set(REMOTE_LIST_URLS_KEY, json.dumps([url.strip()], ensure_ascii=False))

    @staticmethod
    async def set_remote_list_urls(urls: list[str]) -> None:
        """设置远程插件列表 JSON 地址列表"""
        cleaned = [u.strip() for u in urls if u and str(u).strip()]
        await redis_client.set(REMOTE_LIST_URLS_KEY, json.dumps(cleaned, ensure_ascii=False))
        if cleaned:
            await redis_client.set(REMOTE_LIST_URL_KEY, cleaned[0])

    @staticmethod
    def _parse_remote_response(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'plugins' in data:
            return data['plugins']
        if isinstance(data, dict) and 'data' in data:
            return data['data'] if isinstance(data['data'], list) else []
        return []

    @staticmethod
    async def fetch_remote_list() -> list[dict[str, Any]]:
        """从远程 JSON 地址拉取插件列表（支持多 URL 合并，按 name 去重）"""
        urls = await plugin_service.get_remote_list_urls()
        if not urls:
            return []
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=15) as client:
            for url in urls:
                try:
                    resp = await client.get(url.strip())
                    resp.raise_for_status()
                    data = resp.json()
                except Exception:
                    continue
                items = plugin_service._parse_remote_response(data)
                for item in items:
                    name = (item.get('plugin') or {}).get('name') or item.get('name') or ''
                    if isinstance(name, str) and name and name not in seen:
                        seen.add(name)
                        result.append(item)
        return result

    @staticmethod
    async def build(*, plugin: str) -> io.BytesIO:
        """
        打包插件为 zip 压缩包

        :param plugin: 插件名称
        :return:
        """
        plugin_dir = anyio.Path(PLUGIN_DIR / plugin)
        if not await plugin_dir.exists():
            raise errors.NotFoundError(msg='error.plugin_not_found')

        bio = io.BytesIO()
        with zipfile.ZipFile(bio, 'w') as zf:
            for root, dirs, files in os.walk(plugin_dir):
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=plugin_dir)  # noqa: ASYNC240
                    zf.write(file_path, os.path.join(plugin, arcname))

        bio.seek(0)
        return bio


plugin_service: PluginService = PluginService()
