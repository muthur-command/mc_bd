from fastapi import APIRouter

from backend.core.conf import settings
from backend.plugin.card.api.v1.card import router as card_router

v1 = APIRouter(prefix=f'{settings.FASTAPI_API_V1_PATH}/cards', tags=['卡片管理'])

v1.include_router(card_router)
