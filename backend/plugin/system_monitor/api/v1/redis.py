"""Redis 监控 API（由 backend.app.admin.api.v1.monitor.redis 迁移）"""

from fastapi import APIRouter

from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.redis import redis_client
from backend.plugin.system_monitor.schema.monitor import RedisCommandStat, RedisMonitorInfo, RedisServerInfo
from backend.utils.format import fmt_seconds

router = APIRouter()


@router.get('', summary='redis 监控', dependencies=[DependsJwtAuth])
async def get_redis_info() -> ResponseSchemaModel[RedisMonitorInfo]:
    info = await redis_client.info()
    db_size = await redis_client.dbsize()

    uptime_raw = int(info.get('uptime_in_seconds', 0))
    uptime_formatted = fmt_seconds(uptime_raw)

    server_info = RedisServerInfo(
        redis_version=str(info.get('redis_version', '')),
        redis_mode=str(info.get('redis_mode', '')),
        os=str(info.get('os', '')),
        arch_bits=str(info.get('arch_bits', '')),
        tcp_port=str(info.get('tcp_port', '')),
        uptime_seconds=uptime_raw,
        uptime_in_seconds=uptime_formatted,
        connected_clients=str(info.get('connected_clients', '')),
        used_memory_human=str(info.get('used_memory_human', '')),
        used_memory_peak_human=str(info.get('used_memory_peak_human', '')),
        maxmemory_human=str(info.get('maxmemory_human', '0B')),
        keys_num=str(db_size),
    )

    command_stats = await redis_client.info('commandstats')
    stats_list = []
    for key, value in command_stats.items():
        if isinstance(value, dict):
            stats_list.append(RedisCommandStat(name=key.split('_')[-1], value=str(value.get('calls', '0'))))

    data = RedisMonitorInfo(info=server_info, stats=stats_list)
    return response_base.success(data=data)
