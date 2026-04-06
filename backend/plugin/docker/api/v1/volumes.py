"""卷管理API"""

from typing import Annotated

from fastapi import APIRouter, Path

from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.plugin.docker.schema.docker import CreateVolumeParam, VolumeListResponse
from backend.plugin.docker.service.docker_service import docker_service

router = APIRouter()

# 受保护的卷名称列表（不能被删除）
PROTECTED_VOLUMES = ['mc_mysql', 'mc_rabbitmq', 'mc_redis']


@router.get('', summary='获取卷列表', dependencies=[DependsJwtAuth])
async def list_volumes() -> ResponseSchemaModel[list[VolumeListResponse]]:
    """获取卷列表"""
    volumes = docker_service.list_volumes()
    return response_base.success(data=volumes)


@router.post('', summary='创建卷', dependencies=[DependsJwtAuth])
async def create_volume(obj: CreateVolumeParam) -> ResponseModel:
    """创建卷"""
    volume = docker_service.create_volume(
        name=obj.name,
        driver=obj.driver,
        driver_opts=obj.driver_opts,
    )
    return response_base.success(data=volume)


@router.get('/{volume_name}', summary='获取卷详情', dependencies=[DependsJwtAuth])
async def get_volume_detail(
    volume_name: Annotated[str, Path(description='卷名称')],
) -> ResponseSchemaModel[dict]:
    """获取卷详情，包括选项和使用该卷的容器列表"""
    detail = docker_service.get_volume_detail(volume_name)
    return response_base.success(data=detail)


@router.delete('/{volume_name}', summary='删除卷', dependencies=[DependsJwtAuth])
async def remove_volume(
    volume_name: Annotated[str, Path(description='卷名称')],
) -> ResponseModel:
    """删除卷"""
    # 检查是否为受保护的卷
    if volume_name in PROTECTED_VOLUMES:
        return response_base.fail(
            res=CustomResponse(code=400, msg=f'卷 {volume_name} 受保护，无法删除'),
        )
    docker_service.remove_volume(volume_name)
    return response_base.success()
