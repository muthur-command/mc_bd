"""系统监控插件路由：/api/v1/monitors/server、/api/v1/monitors/redis"""

from fastapi import APIRouter

from backend.core.conf import settings
from backend.plugin.system_monitor.api.v1.redis import router as redis_router
from backend.plugin.system_monitor.api.v1.server import router as server_router

v1 = APIRouter(prefix=f'{settings.FASTAPI_API_V1_PATH}/monitors', tags=['系统监控'])

v1.include_router(server_router, prefix='/server', tags=['服务器监控'])
v1.include_router(redis_router, prefix='/redis', tags=['Redis 监控'])
