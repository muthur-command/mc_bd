"""database.redis：RedisCli.init、delete_prefix、get_prefix（无真实连接）。"""

import sys

from unittest.mock import AsyncMock, patch

import pytest

from redis.exceptions import AuthenticationError, TimeoutError

from backend.database.redis import RedisCli


@pytest.mark.asyncio
async def test_redis_cli_init_ping_success() -> None:
    cli = object.__new__(RedisCli)
    cli.ping = AsyncMock()
    await cli.init()
    cli.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_cli_init_timeout_calls_exit() -> None:
    cli = object.__new__(RedisCli)
    cli.ping = AsyncMock(side_effect=TimeoutError())

    with patch.object(sys, 'exit', side_effect=RuntimeError('exit')):
        with pytest.raises(RuntimeError, match='exit'):
            await cli.init()


@pytest.mark.asyncio
async def test_redis_cli_init_auth_error_calls_exit() -> None:
    cli = object.__new__(RedisCli)
    cli.ping = AsyncMock(side_effect=AuthenticationError())

    with patch.object(sys, 'exit', side_effect=RuntimeError('exit')):
        with pytest.raises(RuntimeError, match='exit'):
            await cli.init()


@pytest.mark.asyncio
async def test_delete_prefix_respects_exclude_and_batches() -> None:
    keys = ['p:1', 'p:2', 'p:3', 'p:4']

    async def scan_iter(*, match=None, **kwargs):
        assert match == 'p*'
        for k in keys:
            yield k

    cli = object.__new__(RedisCli)
    cli.scan_iter = scan_iter
    cli.delete = AsyncMock()

    await cli.delete_prefix('p', exclude=['p:2'], batch_size=2)

    assert cli.delete.await_count == 2
    first_call = cli.delete.await_args_list[0].args
    second_call = cli.delete.await_args_list[1].args
    assert set(first_call) == {'p:1', 'p:3'}
    assert set(second_call) == {'p:4'}


@pytest.mark.asyncio
async def test_get_prefix_collects_keys() -> None:
    async def scan_iter(*, match=None, count=100, **kwargs):
        assert match == 'x*'
        assert count == 50
        for k in ['x:a', 'x:b']:
            yield k

    cli = object.__new__(RedisCli)
    cli.scan_iter = scan_iter

    got = await cli.get_prefix('x', count=50)
    assert got == ['x:a', 'x:b']
