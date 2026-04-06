"""镜像源管理API"""

import json

from typing import Annotated

from fastapi import APIRouter, Path
from sqlalchemy import select

from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import (
    ResponseModel,
    ResponseSchemaModel,
    response_base,
)
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import CurrentSession
from backend.plugin.docker.model.docker_config import DockerConfig
from backend.plugin.docker.schema.docker import (
    CreateRegistrySourceParam,
    RegistrySourceResponse,
    UpdateRegistrySourceParam,
)

router = APIRouter()

REGISTRY_CONFIG_KEY = 'docker_registries'
DEFAULT_REGISTRY_ID = 'docker-hub-anonymous'


def _get_default_registries() -> list[dict]:
    """获取默认镜像源列表"""
    return [
        {
            'id': DEFAULT_REGISTRY_ID,
            'name': 'Docker Hub (anonymous)',
            'url': 'docker.io',
            'is_default': True,
        },
    ]


@router.get('', summary='获取镜像源列表', dependencies=[DependsJwtAuth])
async def list_registries(
    db: CurrentSession,
) -> ResponseSchemaModel[list[RegistrySourceResponse]]:
    """获取镜像源列表"""
    try:
        result = await db.execute(select(DockerConfig).where(DockerConfig.key == REGISTRY_CONFIG_KEY))
        config = result.scalar_one_or_none()

        if config:
            registries = json.loads(config.value)
        else:
            # 如果没有配置，返回默认列表
            registries = _get_default_registries()
            # 保存默认配置到数据库
            config = DockerConfig(
                key=REGISTRY_CONFIG_KEY,
                value=json.dumps(registries, ensure_ascii=False),
            )
            db.add(config)
            await db.commit()

        return response_base.success(data=[RegistrySourceResponse(**r) for r in registries])
    except Exception as e:
        return response_base.fail(res=CustomResponse(code=400, msg=f'获取镜像源列表失败: {e!s}'))


@router.post('', summary='添加镜像源', dependencies=[DependsJwtAuth])
async def create_registry(
    obj: CreateRegistrySourceParam,
    db: CurrentSession,
) -> ResponseModel:
    """添加镜像源"""
    try:
        result = await db.execute(select(DockerConfig).where(DockerConfig.key == REGISTRY_CONFIG_KEY))
        config = result.scalar_one_or_none()

        registries = json.loads(config.value) if config else _get_default_registries()

        # 检查名称和URL是否已存在
        for registry in registries:
            if registry['name'] == obj.name:
                return response_base.fail(res=CustomResponse(code=400, msg='镜像源名称已存在'))
            if registry['url'] == obj.url:
                return response_base.fail(res=CustomResponse(code=400, msg='镜像源URL已存在'))

        # 添加新镜像源
        import uuid

        new_registry = {
            'id': f'registry-{uuid.uuid4().hex[:8]}',
            'name': obj.name,
            'url': obj.url,
            'is_default': False,
        }
        registries.append(new_registry)

        if config:
            config.value = json.dumps(registries, ensure_ascii=False)
        else:
            config = DockerConfig(
                key=REGISTRY_CONFIG_KEY,
                value=json.dumps(registries, ensure_ascii=False),
            )
            db.add(config)

        await db.commit()
        return response_base.success()
    except Exception as e:
        await db.rollback()
        return response_base.fail(res=CustomResponse(code=400, msg=f'添加镜像源失败: {e!s}'))


@router.put('/{registry_id}', summary='更新镜像源', dependencies=[DependsJwtAuth])
async def update_registry(
    registry_id: Annotated[str, Path(description='镜像源ID')],
    obj: UpdateRegistrySourceParam,
    db: CurrentSession,
) -> ResponseModel:
    """更新镜像源"""
    try:
        result = await db.execute(select(DockerConfig).where(DockerConfig.key == REGISTRY_CONFIG_KEY))
        config = result.scalar_one_or_none()

        if not config:
            return response_base.fail(res=CustomResponse(code=400, msg='镜像源配置不存在'))

        registries = json.loads(config.value)

        # 查找要更新的镜像源
        registry_index = None
        for i, registry in enumerate(registries):
            if registry['id'] == registry_id:
                registry_index = i
                break

        if registry_index is None:
            return response_base.fail(res=CustomResponse(code=400, msg='镜像源不存在'))

        registry = registries[registry_index]

        # 检查是否为默认镜像源
        if registry.get('is_default'):
            return response_base.fail(res=CustomResponse(code=400, msg='不能修改默认镜像源'))

        # 检查名称和URL是否与其他镜像源冲突
        if obj.name:
            for i, r in enumerate(registries):
                if i != registry_index and r['name'] == obj.name:
                    return response_base.fail(res=CustomResponse(code=400, msg='镜像源名称已存在'))

        if obj.url:
            for i, r in enumerate(registries):
                if i != registry_index and r['url'] == obj.url:
                    return response_base.fail(res=CustomResponse(code=400, msg='镜像源URL已存在'))

        # 更新镜像源
        if obj.name:
            registry['name'] = obj.name
        if obj.url:
            registry['url'] = obj.url

        config.value = json.dumps(registries, ensure_ascii=False)
        await db.commit()
        return response_base.success()
    except Exception as e:
        await db.rollback()
        return response_base.fail(res=CustomResponse(code=400, msg=f'更新镜像源失败: {e!s}'))


@router.delete('/{registry_id}', summary='删除镜像源', dependencies=[DependsJwtAuth])
async def delete_registry(
    registry_id: Annotated[str, Path(description='镜像源ID')],
    db: CurrentSession,
) -> ResponseModel:
    """删除镜像源"""
    try:
        # 使用 with_for_update() 锁定行，防止并发删除导致的竞态条件
        result = await db.execute(select(DockerConfig).where(DockerConfig.key == REGISTRY_CONFIG_KEY).with_for_update())
        config = result.scalar_one_or_none()

        if not config:
            return response_base.fail(res=CustomResponse(code=400, msg='镜像源配置不存在'))

        registries = json.loads(config.value)

        # 查找要删除的镜像源
        registry_to_delete = None
        for registry in registries:
            if registry['id'] == registry_id:
                registry_to_delete = registry
                break

        if not registry_to_delete:
            return response_base.fail(res=CustomResponse(code=400, msg='镜像源不存在'))

        # 检查是否为默认镜像源
        if registry_to_delete.get('is_default'):
            return response_base.fail(res=CustomResponse(code=400, msg='不能删除默认镜像源'))

        # 删除镜像源
        registries = [r for r in registries if r['id'] != registry_id]

        config.value = json.dumps(registries, ensure_ascii=False)
        await db.commit()
        return response_base.success()
    except Exception as e:
        await db.rollback()
        return response_base.fail(res=CustomResponse(code=400, msg=f'删除镜像源失败: {e!s}'))
