"""容器管理API"""

import asyncio

from typing import Annotated

from fastapi import APIRouter, Path, Query, WebSocket, WebSocketDisconnect

from backend.common.log import log
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.plugin.docker.schema.docker import (
    ContainerDetailResponse,
    ContainerListResponse,
    CreateContainerParam,
)
from backend.plugin.docker.service.docker_service import docker_service

router = APIRouter()


@router.get('', summary='获取容器列表', dependencies=[DependsJwtAuth])
async def list_containers(
    *,
    all: Annotated[bool, Query(description='是否包含已停止的容器')] = False,
) -> ResponseSchemaModel[list[ContainerListResponse]]:
    """获取容器列表"""
    containers = docker_service.list_containers(all=all)
    return response_base.success(data=containers)


@router.get('/{container_id}', summary='获取容器详情', dependencies=[DependsJwtAuth])
async def get_container(
    container_id: Annotated[str, Path(description='容器ID或名称')],
) -> ResponseSchemaModel[ContainerDetailResponse]:
    """获取容器详情"""
    container = docker_service.get_container(container_id)
    return response_base.success(data=container)


@router.post('', summary='创建容器', dependencies=[DependsJwtAuth])
async def create_container(obj: CreateContainerParam) -> ResponseModel:
    """创建容器"""
    container = docker_service.create_container(
        image=obj.image,
        name=obj.name,
        command=obj.command,
        entrypoint=obj.entrypoint,
        working_dir=obj.working_dir,
        user=obj.user,
        env=obj.env,
        ports=obj.ports,
        publish_all_ports=obj.publish_all_ports,
        volumes=obj.volumes,
        networks=obj.networks,
        restart_policy=obj.restart_policy,
        labels=obj.labels,
        tty=obj.tty,
        stdin_open=obj.stdin_open,
        auto_remove=obj.auto_remove,
        pull_image=obj.pull_image,
        registry=obj.registry,
    )
    return response_base.success(data=container)


@router.post('/{container_id}/start', summary='启动容器', dependencies=[DependsJwtAuth])
async def start_container(
    container_id: Annotated[str, Path(description='容器ID或名称')],
) -> ResponseModel:
    """启动容器"""
    docker_service.start_container(container_id)
    return response_base.success()


@router.post('/{container_id}/stop', summary='停止容器', dependencies=[DependsJwtAuth])
async def stop_container(
    container_id: Annotated[str, Path(description='容器ID或名称')],
    timeout: Annotated[int, Query(description='超时时间（秒）')] = 10,
) -> ResponseModel:
    """停止容器"""
    docker_service.stop_container(container_id, timeout=timeout)
    return response_base.success()


@router.post('/{container_id}/restart', summary='重启容器', dependencies=[DependsJwtAuth])
async def restart_container(
    container_id: Annotated[str, Path(description='容器ID或名称')],
    timeout: Annotated[int, Query(description='超时时间（秒）')] = 10,
) -> ResponseModel:
    """重启容器"""
    docker_service.restart_container(container_id, timeout=timeout)
    return response_base.success()


@router.post('/{container_id}/pause', summary='暂停容器', dependencies=[DependsJwtAuth])
async def pause_container(
    container_id: Annotated[str, Path(description='容器ID或名称')],
) -> ResponseModel:
    """暂停容器"""
    docker_service.pause_container(container_id)
    return response_base.success()


@router.post('/{container_id}/unpause', summary='恢复容器', dependencies=[DependsJwtAuth])
async def unpause_container(
    container_id: Annotated[str, Path(description='容器ID或名称')],
) -> ResponseModel:
    """恢复容器"""
    docker_service.unpause_container(container_id)
    return response_base.success()


@router.post('/{container_id}/kill', summary='强制停止容器', dependencies=[DependsJwtAuth])
async def kill_container(
    container_id: Annotated[str, Path(description='容器ID或名称')],
    signal: Annotated[str, Query(description='信号')] = 'SIGKILL',
) -> ResponseModel:
    """强制停止容器"""
    docker_service.kill_container(container_id, signal=signal)
    return response_base.success()


@router.delete('/{container_id}', summary='删除容器', dependencies=[DependsJwtAuth])
async def remove_container(
    container_id: Annotated[str, Path(description='容器ID或名称')],
    *,
    force: Annotated[bool, Query(description='是否强制删除运行中的容器')] = False,
) -> ResponseModel:
    """删除容器"""
    docker_service.remove_container(container_id, force=force)
    return response_base.success()


@router.put('/{container_id}/rename', summary='重命名容器', dependencies=[DependsJwtAuth])
async def rename_container(
    container_id: Annotated[str, Path(description='容器ID或名称')],
    new_name: Annotated[str, Query(description='新名称')],
) -> ResponseModel:
    """重命名容器"""
    docker_service.rename_container(container_id, new_name)
    return response_base.success()


@router.put('/{container_id}/restart-policy', summary='更新容器重启策略', dependencies=[DependsJwtAuth])
async def update_container_restart_policy(
    container_id: Annotated[str, Path(description='容器ID或名称')],
    restart_policy: Annotated[str, Query(description='重启策略 (no, always, on-failure, unless-stopped)')],
) -> ResponseModel:
    """更新容器重启策略"""
    docker_service.update_container_restart_policy(container_id, restart_policy)
    return response_base.success()


@router.post('/{container_id}/networks/{network_name}/connect', summary='连接容器到网络', dependencies=[DependsJwtAuth])
async def connect_container_to_network(
    container_id: Annotated[str, Path(description='容器ID或名称')],
    network_name: Annotated[str, Path(description='网络名称')],
) -> ResponseModel:
    """连接容器到网络"""
    docker_service.connect_container_to_network(container_id, network_name)
    return response_base.success()


@router.post(
    '/{container_id}/networks/{network_name}/disconnect', summary='断开容器网络连接', dependencies=[DependsJwtAuth]
)
async def disconnect_container_from_network(
    container_id: Annotated[str, Path(description='容器ID或名称')],
    network_name: Annotated[str, Path(description='网络名称')],
) -> ResponseModel:
    """断开容器网络连接"""
    docker_service.disconnect_container_from_network(container_id, network_name)
    return response_base.success()


@router.get('/{container_id}/logs', summary='获取容器日志', dependencies=[DependsJwtAuth])
async def get_container_logs(
    container_id: Annotated[str, Path(description='容器ID或名称')],
    tail: Annotated[int, Query(description='显示最后N行')] = 100,
    *,
    follow: Annotated[bool, Query(description='是否持续跟踪')] = False,
) -> ResponseSchemaModel[str]:
    """获取容器日志"""
    logs = docker_service.get_container_logs(container_id, tail=tail, follow=follow)
    return response_base.success(data=logs)


@router.websocket('/{container_id}/logs', name='容器日志WebSocket')
async def container_logs_websocket(
    websocket: WebSocket,
    container_id: Annotated[str, Path(description='容器ID或名称')],
) -> None:
    """
    通过WebSocket实时获取容器日志

    连接后，需要发送 {'action': 'start', 'tail': 100} 消息来开始推送日志
    发送 {'action': 'stop'} 消息来停止推送
    """

    log.info(f'[WebSocket] 收到容器日志连接请求: container_id={container_id}')

    try:
        await websocket.accept()
        log.info(f'[WebSocket] WebSocket连接已接受: container_id={container_id}')
    except Exception as e:
        log.error(f'[WebSocket] 接受连接失败: container_id={container_id}, error={e}')
        return

    # 推送状态标志
    is_pushing = False
    loop_count = 0
    last_log_count = 0
    tail_lines = 100  # 默认获取最后100行

    try:
        # 主循环：接收消息并处理
        while True:
            try:
                # 接收客户端消息（非阻塞，设置超时）
                try:
                    message = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)

                    if isinstance(message, dict):
                        action = message.get('action')
                        if action == 'start':
                            if not is_pushing:
                                is_pushing = True
                                loop_count = 0
                                last_log_count = 0
                                tail_lines = message.get('tail', 100)
                                log.info(
                                    f'[WebSocket] 收到启动推送请求: container_id={container_id}, tail={tail_lines}'
                                )
                                await websocket.send_json({
                                    'type': 'control',
                                    'message': '推送已启动',
                                })
                            else:
                                log.info(f'[WebSocket] 推送已在运行中: container_id={container_id}')
                        elif action == 'stop':
                            if is_pushing:
                                is_pushing = False
                                log.info(f'[WebSocket] 收到停止推送请求: container_id={container_id}')
                                await websocket.send_json({
                                    'type': 'control',
                                    'message': '推送已停止',
                                })
                            else:
                                log.info(f'[WebSocket] 推送未运行: container_id={container_id}')
                except asyncio.TimeoutError:
                    # 超时是正常的，继续推送流程
                    pass
                except WebSocketDisconnect:
                    raise
                except Exception as e:
                    log.warning(f'[WebSocket] 接收消息失败: container_id={container_id}, error={e}')

                # 如果正在推送，获取并发送日志
                if is_pushing:
                    try:
                        loop_count += 1
                        if loop_count == 1:
                            log.info(f'[WebSocket] 开始获取容器日志: container_id={container_id}')
                            # 第一次获取，发送全部日志
                            container_logs = docker_service.get_container_logs(
                                container_id, tail=tail_lines, follow=False
                            )
                            log_lines = container_logs.split('\n') if container_logs else []
                            last_log_count = len(log_lines)

                            await websocket.send_json({
                                'type': 'logs',
                                'data': container_logs,
                                'is_initial': True,
                            })
                        else:
                            # 后续轮询，只获取新增的日志
                            # 获取所有日志（使用较大的tail值）
                            all_logs = docker_service.get_container_logs(container_id, tail=10000, follow=False)
                            all_log_lines = all_logs.split('\n') if all_logs else []

                            # 只发送新增的行
                            if len(all_log_lines) > last_log_count:
                                new_lines = all_log_lines[last_log_count:]
                                new_logs = '\n'.join(new_lines)
                                last_log_count = len(all_log_lines)

                                if new_logs.strip():
                                    await websocket.send_json({
                                        'type': 'logs',
                                        'data': new_logs,
                                        'is_initial': False,
                                    })

                        # 等待1秒后发送下一次数据（更频繁的轮询，实现实时效果）
                        await asyncio.sleep(1)
                    except WebSocketDisconnect:
                        raise
                    except Exception as e:
                        log.error(
                            f'[WebSocket] 获取或发送日志失败: container_id={container_id}, error={e}', exc_info=True
                        )
                        await websocket.send_json({
                            'type': 'error',
                            'message': f'获取日志失败: {e!s}',
                        })
                else:
                    # 如果未在推送，短暂等待后继续循环
                    await asyncio.sleep(0.5)
            except WebSocketDisconnect:
                log.info(f'[WebSocket] 客户端断开连接: container_id={container_id}')
                break
            except Exception as e:
                log.error(f'[WebSocket] 处理日志推送时出错: container_id={container_id}, error={e}', exc_info=True)
                break
    except WebSocketDisconnect:
        log.info(f'[WebSocket] WebSocket连接已断开: container_id={container_id}')
    except Exception as e:
        log.error(f'[WebSocket] WebSocket错误: container_id={container_id}, error={e}', exc_info=True)
    finally:
        log.info(f'[WebSocket] 容器日志WebSocket连接已关闭: container_id={container_id}')


@router.websocket('/{container_id}/stats', name='容器统计信息WebSocket')
async def container_stats_websocket(
    websocket: WebSocket,
    container_id: Annotated[str, Path(description='容器ID或名称')],
) -> None:
    """
    通过WebSocket实时获取容器统计信息（CPU、内存、网络、I/O）

    连接后，需要发送 {'action': 'start'} 消息来开始推送统计信息
    发送 {'action': 'stop'} 消息来停止推送
    """
    log.info(f'[WebSocket] 收到容器统计连接请求: container_id={container_id}')

    try:
        await websocket.accept()
        log.info(f'[WebSocket] WebSocket连接已接受: container_id={container_id}')
    except Exception as e:
        log.error(f'[WebSocket] 接受连接失败: container_id={container_id}, error={e}')
        return

    # 推送状态标志
    is_pushing = False
    loop_count = 0

    try:
        # 主循环：接收消息并处理
        while True:
            try:
                # 接收客户端消息（非阻塞，设置超时）
                try:
                    # 使用 asyncio.wait_for 设置超时，避免阻塞
                    message = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)

                    if isinstance(message, dict):
                        action = message.get('action')
                        if action == 'start':
                            if not is_pushing:
                                is_pushing = True
                                loop_count = 0
                                log.info(f'[WebSocket] 收到启动推送请求: container_id={container_id}')
                                await websocket.send_json({
                                    'type': 'control',
                                    'message': '推送已启动',
                                })
                            else:
                                log.info(f'[WebSocket] 推送已在运行中: container_id={container_id}')
                        elif action == 'stop':
                            if is_pushing:
                                is_pushing = False
                                log.info(f'[WebSocket] 收到停止推送请求: container_id={container_id}')
                                await websocket.send_json({
                                    'type': 'control',
                                    'message': '推送已停止',
                                })
                            else:
                                log.info(f'[WebSocket] 推送未运行: container_id={container_id}')
                except asyncio.TimeoutError:
                    # 超时是正常的，继续推送流程
                    pass
                except WebSocketDisconnect:
                    raise
                except Exception as e:
                    log.warning(f'[WebSocket] 接收消息失败: container_id={container_id}, error={e}')

                # 如果正在推送，获取并发送统计信息
                if is_pushing:
                    try:
                        loop_count += 1
                        if loop_count == 1:
                            log.info(f'[WebSocket] 开始获取容器统计信息: container_id={container_id}')

                        # 获取容器统计信息
                        stats = docker_service.get_container_stats(container_id)

                        if loop_count <= 3:
                            log.info(
                                f'[WebSocket] 获取到统计信息 (第{loop_count}次): container_id={container_id}, stats_keys={list(stats.keys()) if isinstance(stats, dict) else "N/A"}'
                            )

                        # 发送统计信息（如果连接断开，这里会抛出 WebSocketDisconnect 异常）
                        await websocket.send_json({
                            'type': 'stats',
                            'data': stats,
                        })

                        # 等待1秒后发送下一次数据
                        await asyncio.sleep(1)
                    except WebSocketDisconnect:
                        raise
                    except Exception as e:
                        log.error(
                            f'[WebSocket] 获取或发送统计信息失败: container_id={container_id}, error={e}', exc_info=True
                        )
                        # 尝试发送错误信息
                        try:
                            await websocket.send_json({
                                'type': 'error',
                                'message': str(e),
                            })
                        except WebSocketDisconnect:
                            raise
                        except:
                            pass
                        # 发生错误时等待更长时间再重试
                        await asyncio.sleep(2)
                else:
                    # 如果未在推送，短暂等待后继续循环
                    await asyncio.sleep(0.5)

            except WebSocketDisconnect:
                # 客户端断开连接，退出循环，停止推送
                log.info(f'[WebSocket] 客户端断开连接，停止推送: container_id={container_id}')
                break

    except WebSocketDisconnect:
        # 客户端断开连接
        log.info(f'[WebSocket] 客户端断开连接: container_id={container_id}')
    except Exception as e:
        # 其他错误，尝试发送错误信息后关闭连接
        log.error(f'[WebSocket] WebSocket连接错误: container_id={container_id}, error={e}', exc_info=True)
        try:
            await websocket.send_json({
                'type': 'error',
                'message': f'连接错误: {e!s}',
            })
        except:
            pass
        finally:
            try:
                await websocket.close()
            except:
                pass
