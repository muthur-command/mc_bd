"""backend.common.model — 类型装饰器与 MappedBase 表名。"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone as dt_timezone
from unittest.mock import MagicMock, patch

from backend.common.model import MappedBase, TimeZone, UniversalText


def test_universal_text_pass_through_bind_result() -> None:
    ut = UniversalText()
    assert ut.process_bind_param('x', None) == 'x'
    assert ut.process_result_value('y', None) == 'y'


def test_timezone_process_result_adds_tz_to_naive() -> None:
    col = TimeZone()
    naive = datetime(2026, 1, 1, 12, 0, 0)
    with patch('backend.common.model.timezone') as tz:
        tz.tz_info = dt_timezone.utc
        out = col.process_result_value(naive, MagicMock())
    assert out.tzinfo is not None


def test_mapped_base_table_name_from_class_name() -> None:
    class SampleWidget(MappedBase):
        """widget doc"""

        __abstract__ = True

    assert SampleWidget.__tablename__ == 'samplewidget'


def test_mapped_base_table_args_comment() -> None:
    class DocModel(MappedBase):
        """my table comment"""

        __abstract__ = True

    args = DocModel.__table_args__
    assert args['comment'] == 'my table comment'
