"""网络管理API"""

from typing import Annotated

from fastapi import APIRouter, Path

from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.plugin.docker.schema.docker import CreateNetworkParam, NetworkListResponse
from backend.plugin.docker.service.docker_service import docker_service

router = APIRouter()

# 受保护的网络名称列表（不能被删除）
PROTECTED_NETWORKS = ['mc_network']


@router.get('', summary='获取网络列表', dependencies=[DependsJwtAuth])
async def list_networks() -> ResponseSchemaModel[list[NetworkListResponse]]:
    """获取网络列表"""
    networks = docker_service.list_networks()
    return response_base.success(data=networks)


@router.post('', summary='创建网络', dependencies=[DependsJwtAuth])
async def create_network(obj: CreateNetworkParam) -> ResponseModel:
    """创建网络"""
    network = docker_service.create_network(
        name=obj.name,
        driver=obj.driver,
        subnet=obj.subnet,
        gateway=obj.gateway,
    )
    return response_base.success(data=network)


@router.delete('/{network_id}', summary='删除网络', dependencies=[DependsJwtAuth])
async def remove_network(
    network_id: Annotated[str, Path(description='网络ID或名称')],
) -> ResponseModel:
    """删除网络"""
    # 检查是否为受保护的网络
    # 先尝试通过 network_id 获取网络信息
    try:
        networks = docker_service.list_networks()
        for network in networks:
            # 检查 ID 或名称是否匹配
            if network['id'] == network_id or network['name'] == network_id:
                if network['name'] in PROTECTED_NETWORKS:
                    return response_base.fail(
                        res=CustomResponse(code=400, msg=f'网络 {network["name"]} 受保护，无法删除'),
                    )
                break
    except Exception:
        # 如果获取网络列表失败，直接尝试删除（让 Docker 处理错误）
        pass

    docker_service.remove_network(network_id)
    return response_base.success()
