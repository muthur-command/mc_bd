from fastapi import APIRouter

from backend.core.conf import settings
from backend.plugin.apprise_notify.api.v1.notify import router as notify_router

v1 = APIRouter(prefix=f'{settings.FASTAPI_API_V1_PATH}/apprise-notify', tags=['Apprise 通知'])

v1.include_router(notify_router)
