from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Path, UploadFile
from fastapi.params import Query
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from backend.app.admin.service.plugin_service import plugin_service
from backend.common.enums import PluginType
from backend.common.exception import errors
from backend.common.i18n import t
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC

router = APIRouter()


class RemoteListUrlBody(BaseModel):
    url: str


class RemoteListUrlsBody(BaseModel):
    urls: list[str]


@router.get('', summary='获取所有插件', dependencies=[DependsJwtAuth])
async def get_all_plugins() -> ResponseSchemaModel[list[dict[str, Any]]]:
    plugins = await plugin_service.get_all()
    return response_base.success(data=plugins)


@router.get('/changed', summary='是否存在插件变更', dependencies=[DependsJwtAuth])
async def plugin_changed() -> ResponseSchemaModel[bool]:
    plugins = await plugin_service.changed()
    return response_base.success(data=bool(plugins))


@router.get('/remote/url', summary='获取远程插件列表地址（单条，兼容）', dependencies=[DependsJwtAuth])
async def get_remote_list_url() -> ResponseSchemaModel[str | None]:
    url = await plugin_service.get_remote_list_url()
    return response_base.success(data=url)


@router.get('/remote/urls', summary='获取远程插件列表地址列表', dependencies=[DependsJwtAuth])
async def get_remote_list_urls() -> ResponseSchemaModel[list[str]]:
    urls = await plugin_service.get_remote_list_urls()
    return response_base.success(data=urls)


@router.put(
    '/remote/url',
    summary='设置远程插件列表地址（单条，兼容）',
    dependencies=[
        Depends(RequestPermission('sys:plugin:edit')),
        DependsRBAC,
    ],
)
async def set_remote_list_url(body: RemoteListUrlBody) -> ResponseModel:
    await plugin_service.set_remote_list_url(body.url)
    return response_base.success()


@router.put(
    '/remote/urls',
    summary='设置远程插件列表地址列表',
    dependencies=[
        Depends(RequestPermission('sys:plugin:edit')),
        DependsRBAC,
    ],
)
async def set_remote_list_urls(body: RemoteListUrlsBody) -> ResponseModel:
    await plugin_service.set_remote_list_urls(body.urls)
    return response_base.success()


@router.get('/remote', summary='获取远程插件列表', dependencies=[DependsJwtAuth])
async def get_remote_list() -> ResponseSchemaModel[list[dict[str, Any]]]:
    try:
        data = await plugin_service.fetch_remote_list()
        return response_base.success(data=data)
    except Exception as e:
        raise errors.RequestError(msg='error.plugin_remote_fetch_failed', data={'detail': str(e)})


@router.post(
    '',
    summary='安装插件',
    description='使用插件 zip 压缩包或 git 仓库地址进行安装（仅开发环境）',
    dependencies=[
        Depends(RequestPermission('sys:plugin:install')),
        DependsRBAC,
    ],
)
async def install_plugin(
    type: Annotated[PluginType, Query(description='插件类型')],
    file: Annotated[UploadFile | None, File()] = None,
    repo_url: Annotated[str | None, Query(description='插件 git 仓库地址')] = None,
) -> ResponseModel:
    plugin_name = await plugin_service.install(type=type, file=file, repo_url=repo_url)
    return response_base.success(
        res=CustomResponse(
            code=200,
            msg=t('success.plugin.install_success', plugin_name=plugin_name),
        ),
    )


@router.delete(
    '/{plugin}',
    summary='卸载插件',
    description='此操作会直接删除插件依赖，但不会直接删除插件，而是将插件移动到备份目录（仅开发环境）',
    dependencies=[
        Depends(RequestPermission('sys:plugin:uninstall')),
        DependsRBAC,
    ],
)
async def uninstall_plugin(plugin: Annotated[str, Path(description='插件名称')]) -> ResponseModel:
    await plugin_service.uninstall(plugin=plugin)
    return response_base.success(
        res=CustomResponse(code=200, msg=t('success.plugin.uninstall_success', plugin_name=plugin)),
    )


@router.put(
    '/{plugin}/status',
    summary='更新插件状态',
    dependencies=[
        Depends(RequestPermission('sys:plugin:edit')),
        DependsRBAC,
    ],
)
async def update_plugin_status(plugin: Annotated[str, Path(description='插件名称')]) -> ResponseModel:
    await plugin_service.update_status(plugin=plugin)
    return response_base.success()


@router.get('/{plugin}', summary='下载插件', dependencies=[DependsJwtAuth])
async def download_plugin(plugin: Annotated[str, Path(description='插件名称')]) -> StreamingResponse:
    bio = await plugin_service.build(plugin=plugin)
    return StreamingResponse(
        bio,
        media_type='application/x-zip-compressed',
        headers={'Content-Disposition': f'attachment; filename={plugin}.zip'},
    )
