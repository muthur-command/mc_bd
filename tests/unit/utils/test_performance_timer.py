"""backend.utils.performance — timer 装饰器。"""

import asyncio

from unittest.mock import patch

import pytest

from backend.utils.performance import timer


@pytest.mark.asyncio
async def test_timer_async_logs_and_returns_value() -> None:
    with patch('backend.utils.performance.log') as log_mock:

        @timer
        async def slow() -> str:
            await asyncio.sleep(0)
            return 'ok'

        assert await slow() == 'ok'
    log_mock.info.assert_called_once()


def test_timer_sync_logs_and_returns_value() -> None:
    with patch('backend.utils.performance.log') as log_mock:

        @timer
        def fast() -> int:
            return 7

        assert fast() == 7
    log_mock.info.assert_called_once()
