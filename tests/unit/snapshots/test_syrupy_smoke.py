"""Syrupy 默认扩展（`McBdSnapshotExtension`）冒烟：有变更时运行 `uv run pytest --snapshot-update`。"""

from __future__ import annotations

from enum import IntEnum

from pydantic import BaseModel


class _Sample(BaseModel):
    name: str
    count: int


class _E(IntEnum):
    A = 1


def test_snapshot_dict(snapshot) -> None:
    assert {"k": "v", "n": 1} == snapshot


def test_snapshot_pydantic_model(snapshot) -> None:
    assert _Sample(name="x", count=2) == snapshot


def test_snapshot_enum(snapshot) -> None:
    assert _E.A == snapshot
