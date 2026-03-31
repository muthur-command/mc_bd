"""卡片管理 API"""

from typing import Any

from fastapi import APIRouter, Depends

from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth

router = APIRouter()


@router.get('/', summary='获取卡片列表', dependencies=[DependsJwtAuth])
async def get_cards() -> ResponseSchemaModel[list[dict[str, Any]]]:
    """获取卡片列表（当前返回空列表，后续可接入 DB 或 Redis）"""
    return response_base.success(data=[])
