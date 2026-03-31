"""Bento 布局插件 API 聚合路由"""

from fastapi import APIRouter

from backend.core.conf import settings
from backend.plugin.bento_layout.api.v1.bento import router as bento_router

v1 = APIRouter(prefix=f'{settings.FASTAPI_API_V1_PATH}/bento-layout', tags=['Bento布局'])

v1.include_router(bento_router)
