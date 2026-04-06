"""mc_bd 默认 Syrupy 扩展：在 Amber 序列化上增加 Pydantic `BaseModel` 等常见类型。"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from syrupy.extensions.amber import AmberDataSerializer, AmberSnapshotExtension
from syrupy.extensions.amber.serializer import AmberDataSerializerPlugin
from syrupy.types import SerializableData


class _PydanticModelPlugin(AmberDataSerializerPlugin):
    @classmethod
    def is_data_serializable(cls, data: SerializableData) -> bool:
        return isinstance(data, BaseModel)

    @classmethod
    def serialize(cls, data: SerializableData, **kwargs: Any) -> str:
        assert isinstance(data, BaseModel)
        normalized = data.model_dump(mode="json")
        return McBdSnapshotSerializer._serialize(normalized, **kwargs)


class _EnumPlugin(AmberDataSerializerPlugin):
    @classmethod
    def is_data_serializable(cls, data: SerializableData) -> bool:
        return isinstance(data, Enum)

    @classmethod
    def serialize(cls, data: SerializableData, **kwargs: Any) -> str:
        assert isinstance(data, Enum)
        return McBdSnapshotSerializer._serialize(data.value, **kwargs)


class _DateTimePlugin(AmberDataSerializerPlugin):
    @classmethod
    def is_data_serializable(cls, data: SerializableData) -> bool:
        return isinstance(data, (datetime, date))

    @classmethod
    def serialize(cls, data: SerializableData, **kwargs: Any) -> str:
        assert isinstance(data, (datetime, date))
        return McBdSnapshotSerializer._serialize(data.isoformat(), **kwargs)


class McBdSnapshotSerializer(AmberDataSerializer):
    """提升 `VERSION` 可在序列化规则变更后一次性使旧快照失效。"""

    VERSION = "mc_bd-1"
    serializer_plugins = (
        _PydanticModelPlugin,
        _EnumPlugin,
        _DateTimePlugin,
    )


class McBdSnapshotExtension(AmberSnapshotExtension):
    """默认快照格式仍为 `.ambr`（Amber），与上游 Syrupy 一致。"""

    serializer_class = McBdSnapshotSerializer
