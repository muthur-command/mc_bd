"""Apprise 通道 CRUD、发送、历史"""

import math

from typing import Annotated, Any

import apprise

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.response.response_schema import ResponseModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import CurrentSession
from backend.plugin.apprise_notify.model.apprise_notify import (
    AppriseNotifyChannelRecord,
    AppriseNotifyLogRecord,
)
from backend.plugin.apprise_notify.service.apprise_send import mask_apprise_url, send_apprise

router = APIRouter(dependencies=[DependsJwtAuth])


class ChannelCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=128)
    apprise_url: str = Field(
        min_length=1,
        validation_alias=AliasChoices('apprise_url', 'appriseUrl'),
    )
    enabled: bool = True
    description: str | None = Field(None, max_length=512)


class ChannelUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(None, min_length=1, max_length=128)
    apprise_url: str | None = Field(None, min_length=1, validation_alias=AliasChoices('apprise_url', 'appriseUrl'))
    enabled: bool | None = None
    description: str | None = Field(None, max_length=512)


class NotifyBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    channel_ids: list[int] = Field(
        min_length=1,
        validation_alias=AliasChoices('channel_ids', 'channelIds'),
    )
    title: str = Field(default='', max_length=255)
    body: str = Field(default='', max_length=16000)


class TestBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = Field(None, max_length=255)
    body: str | None = Field(None, max_length=16000)


def _channel_row(r: AppriseNotifyChannelRecord, *, include_secret: bool) -> dict[str, Any]:
    row: dict[str, Any] = {
        'id': r.id,
        'name': r.name,
        'enabled': r.enabled,
        'description': r.description,
        'appriseUrlMasked': mask_apprise_url(r.apprise_url),
    }
    if include_secret:
        row['appriseUrl'] = r.apprise_url
    return row


def _log_row(r: AppriseNotifyLogRecord) -> dict[str, Any]:
    return {
        'id': r.id,
        'channelId': r.channel_id,
        'channelName': r.channel_name,
        'title': r.title,
        'body': r.body,
        'status': r.status,
        'errorMessage': r.error_message,
        'triggerSource': r.trigger_source or '',
        'createdTime': int(r.created_time.timestamp() * 1000) if r.created_time else 0,
    }


@router.get('/channels', summary='列出 Apprise 通知通道')
async def list_channels(db: CurrentSession) -> ResponseModel:
    result = await db.execute(select(AppriseNotifyChannelRecord).order_by(AppriseNotifyChannelRecord.id.desc()))
    rows = result.scalars().all()
    return response_base.success(data=[_channel_row(r, include_secret=False) for r in rows])


@router.get('/channels/{pk}', summary='获取 Apprise 通知通道详情')
async def get_channel(pk: int, db: CurrentSession) -> ResponseModel:
    r = await db.get(AppriseNotifyChannelRecord, pk)
    if not r:
        raise HTTPException(status_code=404, detail='error.apprise_notify.channel_not_found')
    return response_base.success(data=_channel_row(r, include_secret=True))


@router.post('/channels', summary='创建 Apprise 通知通道')
async def create_channel(data: ChannelCreate, db: CurrentSession) -> ResponseModel:
    obj = apprise.Apprise()
    if not obj.add(data.apprise_url):
        raise HTTPException(status_code=400, detail='error.apprise_notify.invalid_url')
    row = AppriseNotifyChannelRecord(
        name=data.name,
        apprise_url=data.apprise_url,
        enabled=data.enabled,
        description=data.description,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return response_base.success(data=_channel_row(row, include_secret=True))


@router.put('/channels/{pk}', summary='更新 Apprise 通知通道')
async def update_channel(pk: int, data: ChannelUpdate, db: CurrentSession) -> ResponseModel:
    row = await db.get(AppriseNotifyChannelRecord, pk)
    if not row:
        raise HTTPException(status_code=404, detail='error.apprise_notify.channel_not_found')
    if data.apprise_url is not None:
        obj = apprise.Apprise()
        if not obj.add(data.apprise_url):
            raise HTTPException(status_code=400, detail='error.apprise_notify.invalid_url')
        row.apprise_url = data.apprise_url
    if data.name is not None:
        row.name = data.name
    if data.enabled is not None:
        row.enabled = data.enabled
    if data.description is not None:
        row.description = data.description
    await db.commit()
    await db.refresh(row)
    return response_base.success(data=_channel_row(row, include_secret=True))


@router.delete('/channels/{pk}', summary='删除 Apprise 通知通道')
async def delete_channel(pk: int, db: CurrentSession) -> ResponseModel:
    row = await db.get(AppriseNotifyChannelRecord, pk)
    if not row:
        raise HTTPException(status_code=404, detail='error.apprise_notify.channel_not_found')
    await db.delete(row)
    await db.commit()
    return response_base.success(data={'success': True})


async def _append_log(
    db: AsyncSession,
    *,
    channel_id: int | None,
    channel_name: str,
    title: str,
    body: str,
    status: str,
    error_message: str | None,
    trigger_source: str = '',
) -> None:
    log = AppriseNotifyLogRecord(
        channel_id=channel_id,
        channel_name=channel_name,
        title=title,
        body=body,
        status=status,
        error_message=error_message,
        trigger_source=trigger_source or '',
    )
    db.add(log)
    await db.commit()


@router.post('/channels/{pk}/test', summary='测试 Apprise 通知通道')
async def test_channel(
    pk: int,
    data: Annotated[TestBody, Body(default_factory=TestBody)],
    db: CurrentSession,
) -> ResponseModel:
    row = await db.get(AppriseNotifyChannelRecord, pk)
    if not row:
        raise HTTPException(status_code=404, detail='error.apprise_notify.channel_not_found')
    if not row.enabled:
        raise HTTPException(status_code=400, detail='error.apprise_notify.channel_disabled')
    title = data.title or 'Apprise test'
    body = data.body or 'MC backend apprise_notify plugin test message.'
    ok, err = send_apprise(row.apprise_url, title, body)
    await _append_log(
        db,
        channel_id=row.id,
        channel_name=row.name,
        title=title,
        body=body,
        status='success' if ok else 'failed',
        error_message=err,
        trigger_source='test',
    )
    if not ok:
        raise HTTPException(status_code=502, detail='error.apprise_notify.send_failed')
    return response_base.success(data={'success': True})


@router.post('/notify', summary='向指定通道发送通知')
async def notify_channels(data: NotifyBody, db: CurrentSession) -> ResponseModel:
    if not data.channel_ids:
        raise HTTPException(status_code=400, detail='error.apprise_notify.no_channels')

    results: list[dict[str, Any]] = []
    for cid in data.channel_ids:
        row = await db.get(AppriseNotifyChannelRecord, cid)
        if not row:
            results.append({'channelId': cid, 'success': False, 'error': 'not_found'})
            await _append_log(
                db,
                channel_id=cid,
                channel_name='',
                title=data.title,
                body=data.body,
                status='failed',
                error_message='channel_not_found',
                trigger_source='notify',
            )
            continue
        if not row.enabled:
            results.append({'channelId': cid, 'success': False, 'error': 'disabled'})
            await _append_log(
                db,
                channel_id=row.id,
                channel_name=row.name,
                title=data.title,
                body=data.body,
                status='failed',
                error_message='channel_disabled',
                trigger_source='notify',
            )
            continue
        ok, err = send_apprise(row.apprise_url, data.title, data.body)
        await _append_log(
            db,
            channel_id=row.id,
            channel_name=row.name,
            title=data.title,
            body=data.body,
            status='success' if ok else 'failed',
            error_message=err,
            trigger_source='notify',
        )
        results.append({'channelId': cid, 'success': ok, 'error': err})

    all_ok = all(r.get('success') for r in results)
    return response_base.success(data={'results': results, 'allSuccess': all_ok})


@router.get('/logs', summary='分页获取通知发送历史')
async def list_logs(
    db: CurrentSession,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 20,
) -> ResponseModel:
    count_stmt = select(func.count()).select_from(AppriseNotifyLogRecord)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(AppriseNotifyLogRecord).order_by(AppriseNotifyLogRecord.id.desc()).offset((page - 1) * size).limit(size)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    total_pages = math.ceil(total / size) if total else 0

    return response_base.success(
        data={
            'items': [_log_row(r) for r in rows],
            'total': total,
            'page': page,
            'size': size,
            'totalPages': total_pages,
        },
    )
