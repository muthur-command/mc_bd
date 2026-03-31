from fastapi import APIRouter

from backend.app.admin.api.v1.monitor.online import router as token_router

router = APIRouter(prefix='/monitors')

# server、redis 监控已迁移至插件 backend.plugin.system_monitor
router.include_router(token_router, prefix='/sessions', tags=['会话监控'])
