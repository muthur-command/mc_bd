"""Docker 连接状态：AsyncSession 读写 docker_config。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.plugin.docker.model.docker_config import DockerConfig
from backend.plugin.docker.service.docker_service import DockerService


def _scalar_result(row: object | None) -> MagicMock:
    r = MagicMock()
    r.scalar_one_or_none = MagicMock(return_value=row)
    return r


@pytest.mark.asyncio
async def test_get_connected_status_true_when_value_is_true() -> None:
    db = AsyncMock()
    cfg = DockerConfig(key='connected', value='true')
    db.execute = AsyncMock(return_value=_scalar_result(cfg))
    assert await DockerService.get_connected_status(db) is True
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_connected_status_false_when_missing() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result(None))
    assert await DockerService.get_connected_status(db) is False


@pytest.mark.asyncio
async def test_get_connected_status_false_on_exception() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=RuntimeError('db down'))
    assert await DockerService.get_connected_status(db) is False


@pytest.mark.asyncio
async def test_set_connected_status_updates_existing() -> None:
    db = MagicMock()
    cfg = DockerConfig(key='connected', value='false')
    db.execute = AsyncMock(return_value=_scalar_result(cfg))
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    assert await DockerService.set_connected_status(db, True) is True
    assert cfg.value == 'true'
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_set_connected_status_inserts_when_missing() -> None:
    db = MagicMock()
    db.execute = AsyncMock(return_value=_scalar_result(None))
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    assert await DockerService.set_connected_status(db, False) is True
    db.add.assert_called_once()
    added = db.add.call_args[0][0]
    assert isinstance(added, DockerConfig)
    assert added.key == 'connected'
    assert added.value == 'false'
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_connected_status_rollback_on_error() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=RuntimeError('fail'))
    db.rollback = AsyncMock()
    assert await DockerService.set_connected_status(db, True) is False
    db.rollback.assert_awaited_once()
