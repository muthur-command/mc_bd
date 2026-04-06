"""backend.common.queue — batch_dequeue。"""

from __future__ import annotations

import asyncio

import pytest

from backend.common.queue import batch_dequeue


@pytest.mark.asyncio
async def test_batch_dequeue_collects_until_timeout() -> None:
    q: asyncio.Queue[int] = asyncio.Queue()
    await q.put(1)
    await q.put(2)
    got = await batch_dequeue(q, max_items=10, timeout=0.15)
    assert sorted(got) == [1, 2]


@pytest.mark.asyncio
async def test_batch_dequeue_empty_returns_empty_on_timeout() -> None:
    q: asyncio.Queue[int] = asyncio.Queue()
    got = await batch_dequeue(q, max_items=5, timeout=0.05)
    assert got == []
