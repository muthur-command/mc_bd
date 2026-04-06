"""Docker管理插件路由"""

from fastapi import APIRouter

from backend.core.conf import settings
from backend.plugin.docker.api.v1 import (
    containers,
    images,
    networks,
    registries,
    stacks,
    system,
    volumes,
)

v1 = APIRouter(prefix=f'{settings.FASTAPI_API_V1_PATH}/docker', tags=['Docker管理'])

# 容器管理
v1.include_router(containers.router, prefix='/containers', tags=['容器管理'])

# 镜像管理
v1.include_router(images.router, prefix='/images', tags=['镜像管理'])

# 镜像源管理
v1.include_router(registries.router, prefix='/registries', tags=['镜像源管理'])

# 堆栈管理
v1.include_router(stacks.router, prefix='/stacks', tags=['堆栈管理'])

# 网络管理
v1.include_router(networks.router, prefix='/networks', tags=['网络管理'])

# 卷管理
v1.include_router(volumes.router, prefix='/volumes', tags=['卷管理'])

# 系统信息
v1.include_router(system.router, prefix='/system', tags=['系统信息'])
