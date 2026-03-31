"""Bento 布局 CRUD API"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.response.response_schema import response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db
from backend.plugin.bento_layout.model.bento_layout import BentoLayoutRecord

router = APIRouter(dependencies=[DependsJwtAuth])


@router.post('/save', summary='保存 Bento 布局')
async def save_bento_layout(
    data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    page_id = data.get('pageId')
    layout = data.get('layout')
    if not page_id or layout is None:
        raise HTTPException(status_code=400, detail='error.bento_layout.missing_page_or_layout')

    layout_data = json.dumps(layout, ensure_ascii=False)

    result = await db.execute(select(BentoLayoutRecord).where(BentoLayoutRecord.page_id == page_id))
    existing = result.scalars().first()

    if existing:
        existing.layout_data = layout_data
    else:
        db.add(BentoLayoutRecord(page_id=page_id, layout_data=layout_data))

    await db.commit()
    return response_base.success(data={'success': True})


@router.get('/get', summary='获取 Bento 布局')
async def get_bento_layout(
    pageId: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BentoLayoutRecord).where(BentoLayoutRecord.page_id == pageId))
    row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail='error.bento_layout.not_found')

    layout = json.loads(row.layout_data)
    ts = row.updated_time or row.created_time
    timestamp = int(ts.timestamp() * 1000) if ts else 0

    return response_base.success(
        data={
            'layout': layout,
            'pageId': pageId,
            'timestamp': timestamp,
        },
    )


@router.delete('/delete', summary='删除 Bento 布局')
async def delete_bento_layout(
    pageId: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BentoLayoutRecord).where(BentoLayoutRecord.page_id == pageId))
    row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail='error.bento_layout.not_found')

    await db.delete(row)
    await db.commit()
    return response_base.success(data={'success': True})


@router.get('/list', summary='列出已保存的布局')
async def list_bento_layouts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BentoLayoutRecord.page_id, BentoLayoutRecord.updated_time, BentoLayoutRecord.created_time))
    rows = result.all()
    layout_list = []
    for page_id, updated_time, created_time in rows:
        ts = updated_time or created_time
        layout_list.append(
            {
                'pageId': page_id,
                'timestamp': int(ts.timestamp() * 1000) if ts else 0,
            },
        )
    return response_base.success(data=layout_list)
