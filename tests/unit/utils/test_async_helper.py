"""backend.utils.async_helper — run_await。"""

import asyncio

import pytest

from backend.utils.async_helper import run_await


def test_run_await_returns_coroutine_result_in_sync_context() -> None:
    @run_await
    async def coro(x: int) -> int:
        await asyncio.sleep(0)
        return x * 2

    assert coro(21) == 42


def test_run_await_raises_when_wrapped_is_not_async_def() -> None:
    @run_await
    def sync_fn() -> int:
        return 1

    with pytest.raises(TypeError, match='Expected coroutine'):
        sync_fn()
