"""系统信息API"""
from fastapi import APIRouter

from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import CurrentSession
from backend.plugin.docker.schema.docker import (
    ConnectedStatusResponse,
    DiskUsageResponse,
    SetConnectedStatusParam,
    SystemInfoResponse,
)
from backend.plugin.docker.service.docker_service import docker_service

router = APIRouter()


@router.get('/info', summary='获取Docker系统信息', dependencies=[DependsJwtAuth])
async def get_system_info() -> ResponseSchemaModel[SystemInfoResponse]:
    """获取Docker系统信息"""
    info = docker_service.get_system_info()
    return response_base.success(data=info)


@router.get('/df', summary='获取Docker磁盘使用情况', dependencies=[DependsJwtAuth])
async def get_disk_usage() -> ResponseSchemaModel[DiskUsageResponse]:
    """获取Docker磁盘使用情况"""
    usage = docker_service.get_disk_usage()
    return response_base.success(data=usage)


@router.get('/connected', summary='获取连接状态', dependencies=[DependsJwtAuth])
async def get_connected_status(db: CurrentSession) -> ResponseSchemaModel[ConnectedStatusResponse]:
    """获取连接状态"""
    connected = await docker_service.get_connected_status(db)
    return response_base.success(data={'connected': connected})


@router.post('/connected', summary='设置连接状态', dependencies=[DependsJwtAuth])
async def set_connected_status(
    param: SetConnectedStatusParam,
    db: CurrentSession,
) -> ResponseSchemaModel[dict]:
    """设置连接状态"""
    success = await docker_service.set_connected_status(db, param.connected)
    if success:
        return response_base.success(data={'message': '设置成功'})
    return response_base.fail()

