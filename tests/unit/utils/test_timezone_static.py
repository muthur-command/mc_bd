"""backend.utils.timezone — 不依赖配置的静态方法。"""

from datetime import datetime
from datetime import timezone as dt_utc

from backend.utils.timezone import TimeZone


def test_to_utc_from_timestamp() -> None:
    dt = TimeZone.to_utc(0)
    assert dt.tzinfo == dt_utc.utc


def test_to_str_format() -> None:
    s = TimeZone.to_str(datetime(2020, 1, 2, 3, 4, 5, tzinfo=dt_utc.utc))
    assert '2020' in s and '01' in s
