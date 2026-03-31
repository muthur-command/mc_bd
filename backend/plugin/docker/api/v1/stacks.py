"""堆栈管理API (Docker Compose)"""
from typing import Annotated

from fastapi import APIRouter, Path, Query

from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.plugin.docker.schema.docker import (
    DeployStackParam,
    RemoveStackParam,
    StackListResponse,
    StackServicesParam,
    StopStackParam,
)
from backend.plugin.docker.service.docker_service import docker_service

router = APIRouter()


@router.get('', summary='获取堆栈列表', dependencies=[DependsJwtAuth])
async def list_stacks() -> ResponseSchemaModel[list[StackListResponse]]:
    """获取堆栈列表"""
    stacks = docker_service.list_stacks()
    return response_base.success(data=stacks)


@router.post('/deploy', summary='部署堆栈', dependencies=[DependsJwtAuth])
async def deploy_stack(obj: DeployStackParam) -> ResponseModel:
    """部署堆栈（启动Docker Compose）"""
    result = docker_service.deploy_stack(obj.compose_file, obj.project_name)
    return response_base.success(data=result)


@router.post('/stop', summary='停止堆栈', dependencies=[DependsJwtAuth])
async def stop_stack(obj: StopStackParam) -> ResponseModel:
    """停止堆栈"""
    docker_service.stop_stack(obj.project_name, obj.compose_file)
    return response_base.success()


@router.delete('/remove', summary='删除堆栈', dependencies=[DependsJwtAuth])
async def remove_stack(obj: RemoveStackParam) -> ResponseModel:
    """删除堆栈"""
    docker_service.remove_stack(obj.project_name, obj.compose_file, obj.volumes)
    return response_base.success()


@router.get('/services', summary='获取堆栈服务列表', dependencies=[DependsJwtAuth])
async def get_stack_services(
    project_name: Annotated[str, Query(description='项目名称')],
    compose_file: Annotated[str | None, Query(description='Compose文件路径')] = None,
) -> ResponseSchemaModel[list[dict]]:
    """获取堆栈服务列表"""
    services = docker_service.get_stack_services(project_name, compose_file)
    return response_base.success(data=services)

