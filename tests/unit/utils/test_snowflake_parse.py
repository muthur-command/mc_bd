"""backend.utils.snowflake — parse 与手动初始化后的 generate。"""

from backend.utils.snowflake import Snowflake, SnowflakeConfig


def test_snowflake_parse_extracts_components() -> None:
    """手工构造 ID：与 SnowflakeConfig 位布局一致。"""
    ts_ms = 2_000_000_000_000  # 相对 EPOCH 的毫秒时间戳左移前
    timestamp = ts_ms + SnowflakeConfig.EPOCH
    datacenter_id = 3
    worker_id = 5
    sequence = 7
    snowflake_id = (
        (ts_ms << SnowflakeConfig.TIMESTAMP_LEFT_SHIFT)
        | (datacenter_id << SnowflakeConfig.DATACENTER_ID_SHIFT)
        | (worker_id << SnowflakeConfig.WORKER_ID_SHIFT)
        | sequence
    )
    info = Snowflake.parse(snowflake_id)
    assert info.datacenter_id == datacenter_id
    assert info.worker_id == worker_id
    assert info.sequence == sequence
    assert info.timestamp == timestamp


def test_snowflake_generate_after_manual_init() -> None:
    s = Snowflake()
    s._initialized = True  # noqa: SLF001
    s.datacenter_id = 1
    s.worker_id = 2
    s.sequence = 0
    s.last_timestamp = -1
    nid = s.generate()
    info = Snowflake.parse(nid)
    assert info.datacenter_id == 1
    assert info.worker_id == 2
