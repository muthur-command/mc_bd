"""Docker服务层"""
import re
import subprocess
from typing import Any

from python_on_whales import DockerClient, docker
from python_on_whales.exceptions import DockerException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.log import log
from backend.plugin.docker.model.docker_config import DockerConfig


class DockerService:
    """Docker服务类"""

    def __init__(self):
        """初始化Docker客户端"""
        try:
            self.client: DockerClient = docker
        except Exception as e:
            log.error(f'Docker客户端初始化失败: {e}')
            raise

    def _parse_size(self, size_str: str) -> int:
        """
        解析大小字符串为字节数
        例如: "1.2GB" -> 1288490188, "500MB" -> 524288000

        :param size_str: 大小字符串
        :return: 字节数
        """
        if not size_str or size_str == '0B':
            return 0
        
        # 移除空格并转换为大写
        size_str = size_str.strip().upper()
        
        # 单位映射
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4,
        }
        
        # 提取数字和单位
        import re
        match = re.match(r'([\d.]+)\s*([A-Z]+)?', size_str)
        if not match:
            return 0
        
        value = float(match.group(1))
        unit = match.group(2) or 'B'
        
        # 获取单位倍数
        multiplier = units.get(unit, 1)
        
        return int(value * multiplier)

    # ==================== 容器管理 ====================

    def list_containers(self, all: bool = False) -> list[dict[str, Any]]:
        """
        列出所有容器

        :param all: 是否包含已停止的容器
        :return: 容器列表
        """
        try:
            containers = self.client.container.list(all=all)
            result = []
            
            # 获取所有镜像列表，用于通过镜像ID查询tag信息
            image_map = {}
            try:
                images = self.client.image.list(all=True)
                for image in images:
                    image_id = image.id
                    if image_id.startswith('sha256:'):
                        image_id = image_id[7:]
                    # 使用完整ID和短ID（前12位）作为键
                    image_map[image_id] = image.repo_tags if image.repo_tags else []
                    if len(image_id) > 12:
                        image_map[image_id[:12]] = image.repo_tags if image.repo_tags else []
            except Exception as e:
                log.warning(f'获取镜像列表失败: {e}')
                image_map = {}
            
            for container in containers:
                # 使用 inspect 获取详细信息
                inspected = None
                inspected_dict = None
                try:
                    inspected = self.client.container.inspect(container.id)
                    log.debug(f'容器 {container.name} ({container.id[:12]}) inspect 类型: {type(inspected)}')
                    
                    # python-on-whales 可能返回对象或字典，尝试转换为字典
                    if hasattr(inspected, '__dict__'):
                        # 如果是对象，尝试获取其字典表示
                        try:
                            inspected_dict = inspected.__dict__
                            log.debug(f'容器 {container.name} 使用 __dict__ 获取数据')
                        except Exception as e:
                            log.debug(f'容器 {container.name} __dict__ 失败: {e}')
                    if inspected_dict is None and isinstance(inspected, dict):
                        inspected_dict = inspected
                        log.debug(f'容器 {container.name} inspect 是字典类型')
                    elif inspected_dict is None:
                        # 尝试使用 json 方法
                        try:
                            import json
                            inspected_dict = json.loads(json.dumps(inspected, default=str))
                            log.debug(f'容器 {container.name} 使用 json 转换数据')
                        except Exception as e:
                            log.debug(f'容器 {container.name} json 转换失败: {e}')
                    
                    # 记录 inspect 结果的关键字段
                    if inspected_dict:
                        log.debug(f'容器 {container.name} inspect_dict 键: {list(inspected_dict.keys())[:10]}')
                except Exception as e:
                    log.warning(f'获取容器 {container.id} 详细信息失败: {e}')
                    inspected = None
                    inspected_dict = None
                
                # 获取镜像信息 - 通过镜像ID获取tag信息
                image_name = str(container.image) if container.image else 'unknown'
                s_image_id = container.image
                if s_image_id.startswith('sha256:'):
                    s_image_id = s_image_id[7:]
                images = self.client.image.list(all=all)
                for image in images:
                    # 提取镜像ID，去掉 sha256: 前缀，只保留前12个字符
                    image_id = image.id
                    if image_id.startswith('sha256:'):
                        image_id = image_id[7:]
                    if s_image_id == image_id:
                        image_name = image.repo_tags[0] if image.repo_tags else image_id
                
                # 获取端口信息 - 格式化为 "host:container" 格式
                port_mappings = []
                if inspected_dict:
                    # 从 inspect 字典结果获取端口映射
                    network_settings = inspected_dict.get('NetworkSettings') or inspected_dict.get('network_settings')
                    log.debug(f'容器 {container.name} network_settings 类型: {type(network_settings)}, 值: {network_settings is not None}')
                    if network_settings:
                        ports = network_settings.get('Ports') or network_settings.get('ports')
                        log.debug(f'容器 {container.name} ports 类型: {type(ports)}, 值: {ports}')
                        if ports:
                            for container_port, host_ports in ports.items():
                                log.debug(f'容器 {container.name} 端口映射: {container_port} -> {host_ports}')
                                if host_ports:
                                    # host_ports 可能是列表或单个字典
                                    if isinstance(host_ports, list):
                                        for host_port_info in host_ports:
                                            if isinstance(host_port_info, dict):
                                                host_port = host_port_info.get('HostPort', '')
                                                if host_port:
                                                    port_str = f"{host_port}:{container_port.split('/')[0]}"
                                                    port_mappings.append(port_str)
                                                    log.debug(f'容器 {container.name} 添加端口映射: {port_str}')
                                    elif isinstance(host_ports, dict):
                                        host_port = host_ports.get('HostPort', '')
                                        if host_port:
                                            port_str = f"{host_port}:{container_port.split('/')[0]}"
                                            port_mappings.append(port_str)
                                            log.debug(f'容器 {container.name} 添加端口映射: {port_str}')
                
                # 如果 inspected_dict 中没有找到，尝试从 inspected 对象获取
                if not port_mappings and inspected:
                    try:
                        network_settings = getattr(inspected, 'network_settings', None) or getattr(inspected, 'NetworkSettings', None)
                        if network_settings:
                            ports = getattr(network_settings, 'ports', None) or getattr(network_settings, 'Ports', None)
                            if ports:
                                if isinstance(ports, dict):
                                    for container_port, host_ports in ports.items():
                                        if host_ports:
                                            if isinstance(host_ports, list):
                                                for host_port_info in host_ports:
                                                    if isinstance(host_port_info, dict):
                                                        host_port = host_port_info.get('HostPort', '')
                                                        if host_port:
                                                            port_str = f"{host_port}:{container_port.split('/')[0]}"
                                                            port_mappings.append(port_str)
                                            elif isinstance(host_ports, dict):
                                                host_port = host_ports.get('HostPort', '')
                                                if host_port:
                                                    port_str = f"{host_port}:{container_port.split('/')[0]}"
                                                    port_mappings.append(port_str)
                    except Exception as e:
                        log.debug(f'从对象获取端口信息失败: {e}')
                
                # 获取IP地址 - 从网络设置中获取第一个网络的IP
                ip_address = None
                if inspected_dict:
                    network_settings = inspected_dict.get('NetworkSettings') or inspected_dict.get('network_settings')
                    if network_settings:
                        networks = network_settings.get('Networks') or network_settings.get('networks')
                        log.debug(f'容器 {container.name} networks 类型: {type(networks)}, 值: {networks}')
                        if networks:
                            # 获取第一个网络的IP地址
                            for network_name, network_info in networks.items():
                                log.debug(f'容器 {container.name} 网络 {network_name} 信息: {type(network_info)}, {network_info}')
                                if isinstance(network_info, dict):
                                    ip_address = network_info.get('IPAddress') or network_info.get('ip_address')
                                    if ip_address:
                                        log.debug(f'容器 {container.name} 找到IP地址: {ip_address}')
                                        break
                
                # 如果 inspected_dict 中没有找到，尝试从 inspected 对象获取
                if not ip_address and inspected:
                    try:
                        network_settings = getattr(inspected, 'network_settings', None) or getattr(inspected, 'NetworkSettings', None)
                        if network_settings:
                            networks = getattr(network_settings, 'networks', None) or getattr(network_settings, 'Networks', None)
                            if networks:
                                if isinstance(networks, dict):
                                    for network_name, network_info in networks.items():
                                        if hasattr(network_info, 'ip_address'):
                                            ip_address = network_info.ip_address
                                            if ip_address:
                                                break
                                        elif isinstance(network_info, dict):
                                            ip_address = network_info.get('IPAddress') or network_info.get('ip_address')
                                            if ip_address:
                                                break
                    except Exception as e:
                        log.debug(f'从对象获取IP地址失败: {e}')
                
                # 获取堆栈名称 - 从标签中获取 compose project
                stack = None
                if inspected_dict:
                    config = inspected_dict.get('Config') or inspected_dict.get('config')
                    log.debug(f'容器 {container.name} config 类型: {type(config)}, 值: {config is not None}')
                    if config:
                        labels = config.get('Labels') or config.get('labels')
                        log.debug(f'容器 {container.name} labels 类型: {type(labels)}, 值: {labels}')
                        if labels and isinstance(labels, dict):
                            stack = labels.get('com.docker.compose.project') or labels.get('com.docker.compose.project.working_dir')
                            log.debug(f'容器 {container.name} 从标签获取 stack: {stack}')
                            # 如果找到项目目录，提取项目名称
                            if stack and '/' in stack:
                                stack = stack.split('/')[-1]
                                log.debug(f'容器 {container.name} 提取后的 stack: {stack}')
                
                # 如果 inspected_dict 中没有找到，尝试从 inspected 对象获取
                if not stack and inspected:
                    try:
                        config = getattr(inspected, 'config', None) or getattr(inspected, 'Config', None)
                        if config:
                            labels = getattr(config, 'labels', None) or getattr(config, 'Labels', None)
                            if labels:
                                if isinstance(labels, dict):
                                    stack = labels.get('com.docker.compose.project') or labels.get('com.docker.compose.project.working_dir')
                                    if stack and '/' in stack:
                                        stack = stack.split('/')[-1]
                                elif hasattr(labels, 'get'):
                                    stack = labels.get('com.docker.compose.project') or labels.get('com.docker.compose.project.working_dir')
                                    if stack and '/' in stack:
                                        stack = stack.split('/')[-1]
                    except Exception as e:
                        log.debug(f'从对象获取堆栈信息失败: {e}')
                
                # 获取创建时间
                created = None
                if inspected_dict:
                    created = inspected_dict.get('Created') or inspected_dict.get('created')
                if not created and inspected:
                    try:
                        created = getattr(inspected, 'created', None) or getattr(inspected, 'Created', None)
                        if created and hasattr(created, 'isoformat'):
                            created = created.isoformat()
                    except:
                        pass
                if not created and hasattr(container, 'created') and container.created:
                    try:
                        created = container.created.isoformat() if hasattr(container.created, 'isoformat') else str(container.created)
                    except:
                        created = None
                
                # 获取状态
                status = 'unknown'
                if inspected_dict:
                    state = inspected_dict.get('State') or inspected_dict.get('state')
                    if state:
                        if isinstance(state, dict):
                            status = state.get('Status') or state.get('status', 'unknown')
                        else:
                            status = str(state)
                if status == 'unknown' and inspected:
                    try:
                        state = getattr(inspected, 'state', None) or getattr(inspected, 'State', None)
                        if state:
                            if hasattr(state, 'status'):
                                status = state.status
                            elif hasattr(state, 'Status'):
                                status = state.Status
                            elif isinstance(state, dict):
                                status = state.get('Status') or state.get('status', 'unknown')
                    except:
                        pass
                if status == 'unknown' and hasattr(container, 'state'):
                    try:
                        state = container.state
                        if hasattr(state, 'status'):
                            status = state.status
                    except:
                        pass
                
                # 所有权 - 暂时使用默认值，后续可以从用户权限系统获取
                ownership = 'administrators'
                
                container_data = {
                    'id': container.id[:12] if len(container.id) > 12 else container.id,
                    'name': container.name,
                    'image': image_name,
                    'status': status,
                    'created': created,
                    'ports': port_mappings,
                    'stack': stack,
                    'ip_address': ip_address,
                    'ownership': ownership,
                }
                log.info(f'容器 {container.name} 数据: status={status}, ports={len(port_mappings)}, stack={stack}, ip={ip_address}, created={created}')
                result.append(container_data)
            log.info(f'返回 {len(result)} 个容器的数据')
            return result
        except DockerException as e:
            log.error(f'获取容器列表失败: {e}')
            raise

    def get_container(self, container_id: str) -> dict[str, Any]:
        """
        获取容器详情

        :param container_id: 容器ID或名称
        :return: 容器详情
        """
        try:
            import datetime
            import json
            container = self.client.container.inspect(container_id)
            
            # 获取完整容器ID
            full_id = container.id
            
            # 尝试将container对象转换为字典（类似list_containers的逻辑）
            inspected_dict = None
            if hasattr(container, '__dict__'):
                try:
                    inspected_dict = container.__dict__
                except Exception:
                    pass
            if inspected_dict is None and isinstance(container, dict):
                inspected_dict = container
            elif inspected_dict is None:
                try:
                    inspected_dict = json.loads(json.dumps(container, default=str))
                except Exception:
                    pass
            
            # 获取IP地址（从网络设置中获取第一个网络的IP）
            ip_address = None
            if inspected_dict:
                network_settings = inspected_dict.get('NetworkSettings') or inspected_dict.get('network_settings')
                if network_settings:
                    networks = network_settings.get('Networks') or network_settings.get('networks')
                    if networks:
                        for network_name, network_info in networks.items():
                            if isinstance(network_info, dict):
                                ip_address = network_info.get('IPAddress') or network_info.get('ip_address')
                                if ip_address:
                                    break
            
            # 如果 inspected_dict 中没有找到，尝试从 container 对象获取
            if not ip_address:
                try:
                    network_settings = getattr(container, 'network_settings', None) or getattr(container, 'NetworkSettings', None)
                    if network_settings:
                        networks = getattr(network_settings, 'networks', None) or getattr(network_settings, 'Networks', None)
                        if networks:
                            if isinstance(networks, dict):
                                for network_name, network_info in networks.items():
                                    if hasattr(network_info, 'ip_address'):
                                        ip_address = network_info.ip_address
                                        if ip_address:
                                            break
                                    elif isinstance(network_info, dict):
                                        ip_address = network_info.get('IPAddress') or network_info.get('ip_address')
                                        if ip_address:
                                            break
                except Exception as e:
                    log.debug(f'从对象获取IP地址失败: {e}')
            
            # 获取启动时间
            started_at = None
            if inspected_dict:
                state = inspected_dict.get('State') or inspected_dict.get('state')
                if state:
                    started_at = state.get('StartedAt') or state.get('started_at')
            
            if not started_at:
                try:
                    state = getattr(container, 'state', None) or getattr(container, 'State', None)
                    if state:
                        started_at_attr = getattr(state, 'started_at', None) or getattr(state, 'StartedAt', None)
                        if started_at_attr:
                            if hasattr(started_at_attr, 'isoformat'):
                                started_at = started_at_attr.isoformat()
                            else:
                                started_at = str(started_at_attr)
                except Exception as e:
                    log.debug(f'获取启动时间失败: {e}')
            
            # 获取状态
            status = 'unknown'
            if inspected_dict:
                state = inspected_dict.get('State') or inspected_dict.get('state')
                if state:
                    status = state.get('Status') or state.get('status') or 'unknown'
            
            if status == 'unknown':
                try:
                    state = getattr(container, 'state', None) or getattr(container, 'State', None)
                    if state:
                        status = getattr(state, 'status', None) or getattr(state, 'Status', None) or 'unknown'
                except Exception:
                    pass
            
            # 计算运行时长（如果容器正在运行）
            running_for = None
            if started_at and status == 'running':
                try:
                    # 处理ISO格式时间字符串
                    if isinstance(started_at, str):
                        started_at_clean = started_at.replace('Z', '+00:00')
                        start_time = datetime.datetime.fromisoformat(started_at_clean)
                    else:
                        start_time = started_at
                    
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=datetime.timezone.utc)
                    
                    delta = now - start_time
                    total_seconds = int(delta.total_seconds())
                    minutes = total_seconds // 60
                    hours = minutes // 60
                    days = hours // 24
                    
                    if days > 0:
                        running_for = f"{days} days, {hours % 24} hours"
                    elif hours > 0:
                        running_for = f"{hours} hours, {minutes % 60} minutes"
                    else:
                        running_for = f"{minutes} minutes"
                except Exception as e:
                    log.warning(f'计算运行时长失败: {e}')
            
            # 格式化状态文本
            status_text = status
            if running_for and status == 'running':
                status_text = f"Running for {running_for}"
            
            # 获取创建时间
            created = None
            if inspected_dict:
                created = inspected_dict.get('Created') or inspected_dict.get('created')
            
            if not created:
                try:
                    created_attr = getattr(container, 'created', None) or getattr(container, 'Created', None)
                    if created_attr:
                        if hasattr(created_attr, 'isoformat'):
                            created = created_attr.isoformat()
                        else:
                            created = str(created_attr)
                except Exception:
                    pass
            
            # 获取working_dir并转换为字符串
            working_dir = None
            if hasattr(container, 'config') and hasattr(container.config, 'working_dir'):
                working_dir_value = container.config.working_dir
                if working_dir_value is not None:
                    # 如果是Path对象，转换为字符串
                    working_dir = str(working_dir_value)
            
            # 获取镜像SHA256
            image_sha256 = None
            image_full = None
            if inspected_dict:
                image_full = inspected_dict.get('Image') or inspected_dict.get('image')
                if image_full and isinstance(image_full, str) and '@sha256:' in image_full:
                    # 提取SHA256
                    parts = image_full.split('@sha256:')
                    if len(parts) == 2:
                        image_sha256 = parts[1]
            
            if not image_sha256:
                try:
                    image_attr = getattr(container, 'image', None) or getattr(container, 'Image', None)
                    if image_attr:
                        image_full = str(image_attr)
                        if '@sha256:' in image_full:
                            parts = image_full.split('@sha256:')
                            if len(parts) == 2:
                                image_sha256 = parts[1]
                except Exception:
                    pass
            
            # 获取entrypoint
            entrypoint = None
            if inspected_dict:
                config = inspected_dict.get('Config') or inspected_dict.get('config')
                if config:
                    entrypoint = config.get('Entrypoint') or config.get('entrypoint')
            
            if not entrypoint:
                try:
                    if hasattr(container, 'config') and hasattr(container.config, 'entrypoint'):
                        entrypoint_value = container.config.entrypoint
                        if entrypoint_value:
                            entrypoint = entrypoint_value if isinstance(entrypoint_value, list) else [entrypoint_value]
                    elif hasattr(container, 'config') and hasattr(container.config, 'Entrypoint'):
                        entrypoint_value = container.config.Entrypoint
                        if entrypoint_value:
                            entrypoint = entrypoint_value if isinstance(entrypoint_value, list) else [entrypoint_value]
                except Exception:
                    pass
            
            # 获取labels
            labels = None
            if inspected_dict:
                config = inspected_dict.get('Config') or inspected_dict.get('config')
                if config:
                    labels = config.get('Labels') or config.get('labels')
            
            if not labels:
                try:
                    if hasattr(container, 'config') and hasattr(container.config, 'labels'):
                        labels = container.config.labels
                    elif hasattr(container, 'config') and hasattr(container.config, 'Labels'):
                        labels = container.config.Labels
                except Exception:
                    pass
            
            # 获取restart policy
            restart_policy = None
            if inspected_dict:
                host_config = inspected_dict.get('HostConfig') or inspected_dict.get('host_config')
                if host_config:
                    restart_policy_info = host_config.get('RestartPolicy') or host_config.get('restart_policy')
                    if restart_policy_info:
                        if isinstance(restart_policy_info, dict):
                            restart_policy = restart_policy_info.get('Name') or restart_policy_info.get('name')
                        else:
                            restart_policy = str(restart_policy_info)
            
            if not restart_policy:
                try:
                    host_config = getattr(container, 'host_config', None) or getattr(container, 'HostConfig', None)
                    if host_config:
                        restart_policy_attr = getattr(host_config, 'restart_policy', None) or getattr(host_config, 'RestartPolicy', None)
                        if restart_policy_attr:
                            if hasattr(restart_policy_attr, 'name'):
                                restart_policy = restart_policy_attr.name
                            elif hasattr(restart_policy_attr, 'Name'):
                                restart_policy = restart_policy_attr.Name
                            elif isinstance(restart_policy_attr, dict):
                                restart_policy = restart_policy_attr.get('Name') or restart_policy_attr.get('name')
                            else:
                                restart_policy = str(restart_policy_attr)
                except Exception:
                    pass
            
            # 格式化端口配置
            port_configuration = []
            ports_data = container.network_settings.ports if hasattr(container, 'network_settings') and hasattr(container.network_settings, 'ports') else {}
            if ports_data:
                for container_port, host_ports in ports_data.items():
                    if host_ports:
                        if isinstance(host_ports, list):
                            for host_port_info in host_ports:
                                if isinstance(host_port_info, dict):
                                    host_ip = host_port_info.get('HostIp', '0.0.0.0')
                                    host_port = host_port_info.get('HostPort', '')
                                    if host_port:
                                        port_configuration.append(f"{host_ip}:{host_port} -> {container_port}")
                        elif isinstance(host_ports, dict):
                            host_ip = host_ports.get('HostIp', '0.0.0.0')
                            host_port = host_ports.get('HostPort', '')
                            if host_port:
                                port_configuration.append(f"{host_ip}:{host_port} -> {container_port}")
            
            # 格式化镜像信息（包含SHA256）
            image_display = container.config.image if hasattr(container, 'config') and hasattr(container.config, 'image') else ''
            if image_sha256 and image_display:
                image_display = f"{image_display}@sha256:{image_sha256}"
            
            # 获取volumes/mounts信息
            volumes_list = []
            if inspected_dict:
                mounts = inspected_dict.get('Mounts') or inspected_dict.get('mounts')
                if mounts and isinstance(mounts, list):
                    for mount in mounts:
                        if isinstance(mount, dict):
                            source = mount.get('Source') or mount.get('source') or mount.get('Name') or mount.get('name') or ''
                            destination = mount.get('Destination') or mount.get('destination') or ''
                            if source and destination:
                                volumes_list.append({
                                    'host_volume': source,
                                    'container_path': destination,
                                })
            
            if not volumes_list:
                try:
                    mounts_attr = getattr(container, 'mounts', None) or getattr(container, 'Mounts', None)
                    if mounts_attr:
                        if isinstance(mounts_attr, list):
                            for mount in mounts_attr:
                                if hasattr(mount, 'source') or hasattr(mount, 'Source'):
                                    source = getattr(mount, 'source', None) or getattr(mount, 'Source', None) or getattr(mount, 'name', None) or getattr(mount, 'Name', None)
                                    destination = getattr(mount, 'destination', None) or getattr(mount, 'Destination', None)
                                    if source and destination:
                                        volumes_list.append({
                                            'host_volume': str(source),
                                            'container_path': str(destination),
                                        })
                except Exception as e:
                    log.debug(f'获取volumes信息失败: {e}')
            
            # 获取networks信息
            networks_list = []
            if inspected_dict:
                network_settings = inspected_dict.get('NetworkSettings') or inspected_dict.get('network_settings')
                if network_settings:
                    networks = network_settings.get('Networks') or network_settings.get('networks')
                    if networks and isinstance(networks, dict):
                        for network_name, network_info in networks.items():
                            if isinstance(network_info, dict):
                                network_data = {
                                    'network': network_name,
                                    'ip_address': network_info.get('IPAddress') or network_info.get('ip_address') or '',
                                    'gateway': network_info.get('Gateway') or network_info.get('gateway') or '',
                                    'mac_address': network_info.get('MacAddress') or network_info.get('mac_address') or '',
                                }
                                networks_list.append(network_data)
            
            # 如果inspected_dict中没有找到，尝试从container对象获取
            if not networks_list:
                try:
                    network_settings = getattr(container, 'network_settings', None) or getattr(container, 'NetworkSettings', None)
                    if network_settings:
                        networks = getattr(network_settings, 'networks', None) or getattr(network_settings, 'Networks', None)
                        if networks:
                            if isinstance(networks, dict):
                                for network_name, network_info in networks.items():
                                    network_data = {
                                        'network': network_name,
                                        'ip_address': '',
                                        'gateway': '',
                                        'mac_address': '',
                                    }
                                    if hasattr(network_info, 'ip_address') or hasattr(network_info, 'IPAddress'):
                                        network_data['ip_address'] = str(getattr(network_info, 'ip_address', None) or getattr(network_info, 'IPAddress', None) or '')
                                    if hasattr(network_info, 'gateway') or hasattr(network_info, 'Gateway'):
                                        network_data['gateway'] = str(getattr(network_info, 'gateway', None) or getattr(network_info, 'Gateway', None) or '')
                                    if hasattr(network_info, 'mac_address') or hasattr(network_info, 'MacAddress'):
                                        network_data['mac_address'] = str(getattr(network_info, 'mac_address', None) or getattr(network_info, 'MacAddress', None) or '')
                                    networks_list.append(network_data)
                    # 如果还没有找到，使用之前获取的ip_address作为默认网络的IP
                    if not networks_list and ip_address:
                        networks_list.append({
                            'network': 'bridge',
                            'ip_address': ip_address,
                            'gateway': '',
                            'mac_address': '',
                        })
                except Exception as e:
                    log.debug(f'获取networks信息失败: {e}')
            
            return {
                'id': full_id,  # 返回完整ID
                'name': container.name if hasattr(container, 'name') else '',
                'image': image_display,
                'status': status_text,
                'created': created,
                'ports': ports_data,
                'env': container.config.env if hasattr(container, 'config') and hasattr(container.config, 'env') else [],
                'command': container.config.cmd if hasattr(container, 'config') and hasattr(container.config, 'cmd') else None,
                'working_dir': working_dir,
                'ip_address': ip_address,
                'started_at': started_at,
                'running_for': running_for,
                'entrypoint': entrypoint,
                'labels': labels if labels else {},
                'restart_policy': restart_policy or 'no',
                'port_configuration': port_configuration,
                'volumes': volumes_list,
                'networks': networks_list,
            }
        except DockerException as e:
            log.error(f'获取容器详情失败: {e}')
            raise

    def create_container(
        self,
        image: str,
        name: str | None = None,
        command: list[str] | None = None,
        entrypoint: list[str] | None = None,
        working_dir: str | None = None,
        user: str | None = None,
        env: dict[str, str] | None = None,
        ports: dict[str, tuple[int, int]] | None = None,
        publish_all_ports: bool = False,
        volumes: dict[str, dict[str, str]] | None = None,
        networks: list[str] | None = None,
        restart_policy: str = 'no',
        labels: dict[str, str] | None = None,
        tty: bool = True,
        stdin_open: bool = True,
        auto_remove: bool = False,
        pull_image: bool = False,
        registry: str | None = None,
    ) -> dict[str, Any]:
        """
        创建容器

        :param image: 镜像名称
        :param name: 容器名称
        :param command: 启动命令
        :param entrypoint: 入口点
        :param working_dir: 工作目录
        :param user: 运行用户
        :param env: 环境变量
        :param ports: 端口映射 {容器端口: (主机IP, 主机端口)}
        :param publish_all_ports: 是否发布所有暴露的端口到随机主机端口
        :param volumes: 卷映射
        :param networks: 网络列表
        :param restart_policy: 重启策略 (no, always, on-failure, unless-stopped)
        :param labels: 标签
        :param tty: 是否分配伪终端
        :param stdin_open: 是否保持标准输入打开
        :param auto_remove: 容器退出时自动删除
        :param pull_image: 是否在创建前拉取镜像
        :param registry: 镜像源ID（用于拉取镜像）
        :return: 创建的容器信息
        """
        try:
            # 如果需要拉取镜像
            if pull_image:
                try:
                    # 如果指定了 registry，需要从对应的镜像源拉取
                    # 这里简化处理，直接拉取镜像
                    self.client.image.pull(image)
                    log.info(f'成功拉取镜像: {image}')
                except DockerException as e:
                    log.warning(f'拉取镜像失败，尝试使用本地镜像: {e}')
                    # 如果拉取失败，继续使用本地镜像

            # 构建创建参数
            create_kwargs: dict[str, Any] = {
                'image': image,
                'tty': tty,
                'stdin_open': stdin_open,
                'detach': True,  # 后台运行
            }

            if name:
                create_kwargs['name'] = name

            if command:
                create_kwargs['command'] = command

            if entrypoint:
                create_kwargs['entrypoint'] = entrypoint

            if working_dir:
                create_kwargs['workdir'] = working_dir

            if user:
                create_kwargs['user'] = user

            if env:
                create_kwargs['envs'] = env

            if ports:
                create_kwargs['publish'] = ports
            elif publish_all_ports:
                # 如果启用发布所有端口，需要先获取镜像暴露的端口
                # 这里简化处理，使用 publish_all=True
                create_kwargs['publish_all'] = True

            if volumes:
                create_kwargs['volumes'] = volumes

            if networks:
                create_kwargs['networks'] = networks

            if restart_policy and restart_policy != 'no':
                create_kwargs['restart'] = restart_policy

            if labels:
                create_kwargs['labels'] = labels

            # 注意：auto_remove 在 python_on_whales 中需要在容器退出时处理
            # 这里先创建容器，如果需要 auto_remove，可以在容器退出时自动删除
            # 但 python_on_whales 的 container.create 不支持 remove 参数
            # 如果需要 auto_remove，需要在容器退出时手动删除

            container = self.client.container.create(**create_kwargs)
            
            # 如果设置了 auto_remove，需要在容器退出时自动删除
            # 这需要在容器退出时通过事件监听或回调来实现
            # 目前先创建容器，后续可以添加事件监听
            return {
                'id': container.id[:12],
                'name': container.name,
            }
        except DockerException as e:
            log.error(f'创建容器失败: {e}')
            raise

    def start_container(self, container_id: str) -> bool:
        """
        启动容器

        :param container_id: 容器ID或名称
        :return: 是否成功
        """
        try:
            container = self.client.container.inspect(container_id)
            container.start()
            return True
        except DockerException as e:
            log.error(f'启动容器失败: {e}')
            raise

    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """
        停止容器

        :param container_id: 容器ID或名称
        :param timeout: 超时时间（秒）
        :return: 是否成功
        """
        try:
            container = self.client.container.inspect(container_id)
            # python-on-whales 的 stop 方法可能使用 time 参数而不是 timeout
            try:
                container.stop(time=timeout)
            except TypeError:
                # 如果不支持 time 参数，尝试不使用参数
                container.stop()
            return True
        except DockerException as e:
            log.error(f'停止容器失败: {e}')
            raise

    def restart_container(self, container_id: str, timeout: int = 10) -> bool:
        """
        重启容器

        :param container_id: 容器ID或名称
        :param timeout: 超时时间（秒）（python-on-whales 的 restart 方法不支持此参数，保留用于API兼容性）
        :return: 是否成功
        """
        try:
            container = self.client.container.inspect(container_id)
            # python-on-whales 的 restart 方法不支持 timeout 参数
            container.restart()
            return True
        except DockerException as e:
            log.error(f'重启容器失败: {e}')
            raise

    def pause_container(self, container_id: str) -> bool:
        """
        暂停容器

        :param container_id: 容器ID或名称
        :return: 是否成功
        """
        try:
            container = self.client.container.inspect(container_id)
            container.pause()
            return True
        except DockerException as e:
            log.error(f'暂停容器失败: {e}')
            raise

    def unpause_container(self, container_id: str) -> bool:
        """
        恢复容器

        :param container_id: 容器ID或名称
        :return: 是否成功
        """
        try:
            container = self.client.container.inspect(container_id)
            container.unpause()
            return True
        except DockerException as e:
            log.error(f'恢复容器失败: {e}')
            raise

    def kill_container(self, container_id: str, signal: str = 'SIGKILL') -> bool:
        """
        强制停止容器

        :param container_id: 容器ID或名称
        :param signal: 信号（默认SIGKILL）
        :return: 是否成功
        """
        try:
            container = self.client.container.inspect(container_id)
            container.kill(signal=signal)
            return True
        except DockerException as e:
            log.error(f'强制停止容器失败: {e}')
            raise

    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """
        删除容器

        :param container_id: 容器ID或名称
        :param force: 是否强制删除运行中的容器
        :return: 是否成功
        """
        try:
            container = self.client.container.inspect(container_id)
            container.remove(force=force)
            return True
        except DockerException as e:
            log.error(f'删除容器失败: {e}')
            raise

    def rename_container(self, container_id: str, new_name: str) -> bool:
        """
        重命名容器

        :param container_id: 容器ID或名称
        :param new_name: 新名称
        :return: 是否成功
        """
        try:
            container = self.client.container.inspect(container_id)
            container.rename(new_name)
            return True
        except DockerException as e:
            log.error(f'重命名容器失败: {e}')
            raise

    def update_container_restart_policy(self, container_id: str, restart_policy: str) -> bool:
        """
        更新容器的重启策略

        :param container_id: 容器ID或名称
        :param restart_policy: 重启策略 (no, always, on-failure, unless-stopped)
        :return: 是否成功
        """
        try:
            # 使用 docker update 命令更新容器的重启策略
            # python-on-whales 可能没有直接的 update 方法，使用 subprocess 调用 docker update
            result = subprocess.run(
                ['docker', 'update', '--restart', restart_policy, container_id],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except DockerException as e:
            log.error(f'更新容器重启策略失败: {e}')
            raise
        except subprocess.CalledProcessError as e:
            log.error(f'更新容器重启策略失败: {e.stderr}')
            raise
        except Exception as e:
            log.error(f'更新容器重启策略失败: {e}')
            raise

    def connect_container_to_network(self, container_id: str, network_name: str) -> bool:
        """
        将容器连接到网络

        :param container_id: 容器ID或名称
        :param network_name: 网络名称
        :return: 是否成功
        """
        try:
            container = self.client.container.inspect(container_id)
            network = self.client.network.inspect(network_name)
            network.connect(container_id)
            return True
        except DockerException as e:
            log.error(f'连接容器到网络失败: {e}')
            raise

    def disconnect_container_from_network(self, container_id: str, network_name: str) -> bool:
        """
        将容器从网络断开

        :param container_id: 容器ID或名称
        :param network_name: 网络名称
        :return: 是否成功
        """
        try:
            container = self.client.container.inspect(container_id)
            network = self.client.network.inspect(network_name)
            network.disconnect(container_id)
            return True
        except DockerException as e:
            log.error(f'断开容器网络连接失败: {e}')
            raise

    def get_container_logs(self, container_id: str, tail: int = 100, follow: bool = False) -> str:
        """
        获取容器日志

        :param container_id: 容器ID或名称
        :param tail: 显示最后N行，0表示获取所有日志
        :param follow: 是否持续跟踪（保留参数以兼容API，但实际不使用，因为使用轮询方式）
        :return: 日志内容
        """
        try:
            container = self.client.container.inspect(container_id)
            # python_on_whales 的 logs() 方法不支持 follow 参数，只支持 tail 参数
            # 如果 tail 为 0，使用一个较大的数字来获取所有日志
            # 如果 tail 很大（>10000），也限制为 10000 以避免内存问题
            actual_tail = 10000 if tail == 0 or tail > 10000 else tail
            logs = container.logs(tail=actual_tail)
            if isinstance(logs, str):
                return logs
            # 使用 errors='replace' 来处理无法解码的字符，避免显示为方块
            # 这样无法解码的字符会被替换为 U+FFFD () 字符
            # 也可以使用 errors='ignore' 来直接忽略无法解码的字符
            return logs.decode('utf-8', errors='replace')
        except DockerException as e:
            log.error(f'获取容器日志失败: {e}')
            raise

    def get_container_stats(self, container_id: str) -> dict[str, Any]:
        """
        获取容器统计信息（CPU、内存、网络、I/O）

        :param container_id: 容器ID或名称
        :return: 容器统计信息
        """
        try:
            # 获取容器统计信息
            # python-on-whales的stats()可能返回生成器、列表或字典
            stats_result = self.client.container.stats(container_id)
            
            # 处理不同的返回类型
            if isinstance(stats_result, dict):
                # 直接是字典
                stats = stats_result
            elif isinstance(stats_result, list):
                # 是列表，取第一个元素
                if not stats_result:
                    raise DockerException(f'无法获取容器 {container_id} 的统计信息')
                stats = stats_result[0]
            elif hasattr(stats_result, '__iter__') and not isinstance(stats_result, (str, bytes)):
                # 是生成器或迭代器，取第一个元素
                try:
                    stats = next(stats_result)
                except StopIteration:
                    raise DockerException(f'无法获取容器 {container_id} 的统计信息')
            else:
                # 其他类型，直接使用
                stats = stats_result
            
            # python-on-whales返回的stats可能是字典或对象
            # 先尝试作为字典处理
            if isinstance(stats, dict):
                stats_dict = stats
            else:
                # 如果是对象，尝试转换为字典
                if hasattr(stats, '__dict__'):
                    stats_dict = stats.__dict__
                elif hasattr(stats, 'model_dump'):  # Pydantic模型
                    stats_dict = stats.model_dump()
                elif hasattr(stats, 'dict'):  # Pydantic v1
                    stats_dict = stats.dict()
                else:
                    # 尝试使用vars()或直接访问属性
                    try:
                        stats_dict = vars(stats) if hasattr(vars, '__call__') else {}
                    except:
                        stats_dict = {}
            
            # 调试：记录原始数据结构（始终记录，直到问题解决）
            if not hasattr(self, '_stats_debug_count'):
                self._stats_debug_count = 0
            self._stats_debug_count += 1
            
            log.info(f'[容器统计调试] stats_result类型: {type(stats_result)}')
            log.info(f'[容器统计调试] stats类型: {type(stats)}')
            log.info(f'[容器统计调试] stats_dict类型: {type(stats_dict)}')
            if isinstance(stats_dict, dict):
                log.info(f'[容器统计调试] stats_dict的键: {list(stats_dict.keys())[:30]}')
                log.info(f'[容器统计调试] stats_dict包含cpu_stats: {"cpu_stats" in stats_dict}')
                log.info(f'[容器统计调试] stats_dict包含memory_stats: {"memory_stats" in stats_dict}')
                log.info(f'[容器统计调试] stats_dict包含networks: {"networks" in stats_dict}')
                log.info(f'[容器统计调试] stats_dict包含blkio_stats: {"blkio_stats" in stats_dict}')
                
                # 输出关键字段的详细信息
                if 'cpu_stats' in stats_dict:
                    cpu_stats_val = stats_dict['cpu_stats']
                    log.info(f'[容器统计调试] cpu_stats类型: {type(cpu_stats_val)}, 值: {str(cpu_stats_val)[:500]}')
                if 'memory_stats' in stats_dict:
                    memory_stats_val = stats_dict['memory_stats']
                    log.info(f'[容器统计调试] memory_stats类型: {type(memory_stats_val)}, 值: {str(memory_stats_val)[:500]}')
                if 'networks' in stats_dict:
                    networks_val = stats_dict['networks']
                    log.info(f'[容器统计调试] networks类型: {type(networks_val)}, 值: {str(networks_val)[:500]}')
                
                # 输出部分原始数据
                import json
                try:
                    stats_json = json.dumps(stats_dict, default=str, ensure_ascii=False)[:3000]
                    log.info(f'[容器统计调试] stats_dict前3000字符: {stats_json}')
                except:
                    log.info(f'[容器统计调试] stats_dict字符串（前3000字符）: {str(stats_dict)[:3000]}')
            else:
                log.info(f'[容器统计调试] stats_dict不是字典类型，无法获取键')
            
            # python-on-whales返回的数据格式与Docker API不同，直接使用其提供的字段
            # 检查是否是python-on-whales格式（包含cpu_percentage字段）
            if isinstance(stats_dict, dict) and 'cpu_percentage' in stats_dict:
                # python-on-whales格式：直接使用已计算的字段
                cpu_percent = float(stats_dict.get('cpu_percentage', 0.0))
                memory_usage = int(stats_dict.get('memory_used', 0))
                memory_limit = int(stats_dict.get('memory_limit', 0))
                memory_percent = float(stats_dict.get('memory_percentage', 0.0))
                network_rx = int(stats_dict.get('net_download', 0))
                network_tx = int(stats_dict.get('net_upload', 0))
                io_read = int(stats_dict.get('block_read', 0))
                io_write = int(stats_dict.get('block_write', 0))
            else:
                # Docker API原始格式：需要解析计算
                # 解析CPU使用率
                cpu_percent = 0.0
                cpu_stats = stats_dict.get('cpu_stats', {}) if isinstance(stats_dict, dict) else getattr(stats, 'cpu_stats', None)
                precpu_stats = stats_dict.get('precpu_stats', {}) if isinstance(stats_dict, dict) else getattr(stats, 'precpu_stats', None)
                
                if cpu_stats and precpu_stats:
                    if isinstance(cpu_stats, dict):
                        cpu_usage = cpu_stats.get('cpu_usage', {})
                        precpu_usage = precpu_stats.get('cpu_usage', {}) if isinstance(precpu_stats, dict) else {}
                        cpu_delta = cpu_usage.get('total_usage', 0) - precpu_usage.get('total_usage', 0)
                        system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)
                        num_cpus = cpu_stats.get('online_cpus', 1)
                    else:
                        cpu_usage = getattr(cpu_stats, 'cpu_usage', {})
                        precpu_usage = getattr(precpu_stats, 'cpu_usage', {})
                        cpu_delta = getattr(cpu_usage, 'total_usage', 0) - getattr(precpu_usage, 'total_usage', 0)
                        system_delta = getattr(cpu_stats, 'system_cpu_usage', 0) - getattr(precpu_stats, 'system_cpu_usage', 0)
                        num_cpus = getattr(cpu_stats, 'online_cpus', 1)
                    
                    if system_delta > 0 and num_cpus > 0:
                        cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
                
                # 解析内存使用
                memory_usage = 0
                memory_limit = 0
                memory_percent = 0.0
                memory_stats = stats_dict.get('memory_stats', {}) if isinstance(stats_dict, dict) else getattr(stats, 'memory_stats', None)
                
                if memory_stats:
                    if isinstance(memory_stats, dict):
                        memory_usage = memory_stats.get('usage', 0) or memory_stats.get('rss', 0) or 0
                        memory_limit = memory_stats.get('limit', 0) or memory_stats.get('max_usage', 0) or 0
                        # 如果limit为0，尝试从其他字段获取
                        if memory_limit == 0 and 'stats' in memory_stats:
                            memory_limit = memory_stats['stats'].get('hierarchical_memory_limit', 0)
                    else:
                        memory_usage = getattr(memory_stats, 'usage', None) or getattr(memory_stats, 'rss', 0) or 0
                        memory_limit = getattr(memory_stats, 'limit', None) or getattr(memory_stats, 'max_usage', 0) or 0
                    
                    if memory_limit > 0:
                        memory_percent = (memory_usage / memory_limit) * 100.0
                
                # 解析网络统计
                network_rx = 0
                network_tx = 0
                networks = stats_dict.get('networks', {}) if isinstance(stats_dict, dict) else getattr(stats, 'networks', None)
                
                if networks:
                    if isinstance(networks, dict):
                        for network_name, network_data in networks.items():
                            if isinstance(network_data, dict):
                                network_rx += network_data.get('rx_bytes', 0)
                                network_tx += network_data.get('tx_bytes', 0)
                            else:
                                network_rx += getattr(network_data, 'rx_bytes', 0)
                                network_tx += getattr(network_data, 'tx_bytes', 0)
                
                # 解析I/O统计
                io_read = 0
                io_write = 0
                blkio_stats = stats_dict.get('blkio_stats', {}) if isinstance(stats_dict, dict) else getattr(stats, 'blkio_stats', None)
                
                if blkio_stats:
                    io_service_bytes = None
                    if isinstance(blkio_stats, dict):
                        io_service_bytes = blkio_stats.get('io_service_bytes_recursive', [])
                    else:
                        io_service_bytes = getattr(blkio_stats, 'io_service_bytes_recursive', [])
                    
                    if io_service_bytes:
                        for entry in io_service_bytes:
                            if isinstance(entry, dict):
                                op = entry.get('op', '')
                                value = entry.get('value', 0)
                            else:
                                op = getattr(entry, 'op', '')
                                value = getattr(entry, 'value', 0)
                            
                            if op == 'Read':
                                io_read += value
                            elif op == 'Write':
                                io_write += value
            
            # 获取时间戳
            timestamp = None
            if isinstance(stats_dict, dict):
                read_time = stats_dict.get('read')
                if read_time:
                    timestamp = read_time.isoformat() if hasattr(read_time, 'isoformat') else str(read_time)
            else:
                read_time = getattr(stats, 'read', None)
                if read_time:
                    timestamp = read_time.isoformat() if hasattr(read_time, 'isoformat') else str(read_time)
            
            result = {
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage': memory_usage,
                'memory_limit': memory_limit,
                'memory_percent': round(memory_percent, 2),
                'network_rx': network_rx,
                'network_tx': network_tx,
                'io_read': io_read,
                'io_write': io_write,
                'timestamp': timestamp,
            }
            
            # 调试：记录解析后的结果（始终记录，直到问题解决）
            log.info(f'[容器统计调试] 解析后的结果: cpu_percent={result["cpu_percent"]}, memory_usage={result["memory_usage"]}, memory_limit={result["memory_limit"]}, memory_percent={result["memory_percent"]}, network_rx={result["network_rx"]}, network_tx={result["network_tx"]}, io_read={result["io_read"]}, io_write={result["io_write"]}')
            
            return result
        except DockerException as e:
            log.error(f'获取容器统计信息失败: {e}')
            raise
        except Exception as e:
            log.error(f'解析容器统计信息失败: {e}')
            raise

    # ==================== 镜像管理 ====================

    def list_images(self, all: bool = False) -> list[dict[str, Any]]:
        """
        列出所有镜像

        :param all: 是否包含中间镜像
        :return: 镜像列表
        """
        try:
            images = self.client.image.list(all=all)
            result = []
            for image in images:
                # 提取镜像ID，去掉 sha256: 前缀，只保留前12个字符
                image_id = image.id
                if image_id.startswith('sha256:'):
                    image_id = image_id[7:]
                image_id = image_id[:12] if len(image_id) > 12 else image_id
                
                result.append({
                    'id': image_id,
                    'tags': image.repo_tags,
                    'size': image.size,
                    'created': image.created.isoformat() if image.created else None,
                })
            return result
        except DockerException as e:
            log.error(f'获取镜像列表失败: {e}')
            raise

    def pull_image(self, image: str, tag: str = 'latest') -> dict[str, Any]:
        """
        拉取镜像

        :param image: 镜像名称
        :param tag: 标签
        :return: 镜像信息
        """
        try:
            full_image = f'{image}:{tag}' if tag else image
            pulled_image = self.client.image.pull(full_image)
            return {
                'id': pulled_image.id,
                'tags': pulled_image.repo_tags,
            }
        except DockerException as e:
            log.error(f'拉取镜像失败: {e}')
            raise

    def remove_image(self, image_id: str, force: bool = False) -> bool:
        """
        删除镜像

        :param image_id: 镜像ID或名称
        :param force: 是否强制删除
        :return: 是否成功
        """
        try:
            self.client.image.remove(image_id, force=force)
            return True
        except DockerException as e:
            log.error(f'删除镜像失败: {e}')
            raise

    def build_image(
        self,
        path: str,
        tag: str,
        dockerfile: str = 'Dockerfile',
        build_args: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        构建镜像

        :param path: 构建上下文路径
        :param tag: 镜像标签
        :param dockerfile: Dockerfile路径
        :param build_args: 构建参数
        :return: 构建的镜像信息
        """
        try:
            built_image = self.client.build(
                path=path,
                tags=[tag],
                file=dockerfile,
                build_args=build_args,
            )
            return {
                'id': built_image.id,
                'tags': built_image.repo_tags,
            }
        except DockerException as e:
            log.error(f'构建镜像失败: {e}')
            raise

    def build_image_from_tar(
        self,
        tar_data: bytes,
        tag: str,
        dockerfile: str = 'Dockerfile',
        build_args: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        从 tar 文件构建镜像

        :param tar_data: tar 文件的字节数据（包含构建上下文和 Dockerfile）
        :param tag: 镜像标签
        :param dockerfile: Dockerfile路径（相对于构建上下文）
        :param build_args: 构建参数
        :return: 构建的镜像信息
        """
        try:
            import tempfile
            import os
            
            # 创建临时目录保存构建上下文
            with tempfile.TemporaryDirectory() as temp_dir:
                # 解压 tar 文件到临时目录
                import tarfile
                from io import BytesIO
                
                tar_stream = BytesIO(tar_data)
                with tarfile.open(fileobj=tar_stream, mode='r:*') as tar:
                    tar.extractall(path=temp_dir)
                
                # 使用临时目录作为构建上下文
                built_image = self.client.build(
                    path=temp_dir,
                    tags=[tag],
                    file=dockerfile,
                    build_args=build_args,
                )
                
                return {
                    'id': built_image.id,
                    'tags': built_image.repo_tags,
                }
        except DockerException as e:
            log.error(f'从 tar 文件构建镜像失败: {e}')
            raise
        except Exception as e:
            log.error(f'从 tar 文件构建镜像时发生未知错误: {e}')
            raise

    def save_image(self, image_id: str) -> bytes:
        """
        导出镜像为 tar 文件

        :param image_id: 镜像ID或名称（优先使用 tag，如果没有 tag 则使用 ID）
        :return: tar 文件的字节数据
        """
        try:
            from io import BytesIO
            
            # 如果传入的是镜像 ID，尝试查找对应的镜像以获取 tag
            image_identifier = image_id
            try:
                # 尝试通过镜像 ID 查找镜像对象
                images = self.client.image.list(all=True)
                for img in images:
                    # 检查是否是匹配的镜像 ID（前12位或完整 ID）
                    if (img.id.startswith(image_id) or 
                        image_id.startswith(img.id[:12]) or
                        img.id[:12] == image_id):
                        # 如果镜像有 tag，优先使用 tag 导出（这样可以保留 tag 信息）
                        if img.repo_tags and len(img.repo_tags) > 0:
                            # 使用第一个 tag
                            image_identifier = img.repo_tags[0]
                            log.info(f'使用镜像 tag 导出: {image_identifier} (原 ID: {image_id})')
                            break
            except Exception as e:
                log.warning(f'查找镜像 tag 失败，使用原始 ID: {e}')
                # 如果查找失败，继续使用原始 image_id
            
            # 使用 subprocess 调用 docker save 命令导出镜像
            result = subprocess.run(
                ['docker', 'save', image_identifier],
                capture_output=True,
                check=True,
            )
            
            return result.stdout
        except subprocess.CalledProcessError as e:
            log.error(f'导出镜像失败: {e.stderr.decode() if e.stderr else str(e)}')
            raise DockerException(f'导出镜像失败: {e.stderr.decode() if e.stderr else str(e)}')
        except Exception as e:
            log.error(f'导出镜像失败: {e}')
            raise

    def load_image(self, tar_data: bytes) -> dict[str, Any]:
        """
        从 tar 文件导入镜像

        :param tar_data: tar 文件的字节数据
        :return: 导入的镜像信息
        """
        try:
            import tempfile
            import os
            
            # 创建临时文件保存 tar 数据
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tar') as tmp_file:
                tmp_file.write(tar_data)
                tmp_path = tmp_file.name
            
            try:
                # 使用 subprocess 调用 docker load 命令导入镜像
                result = subprocess.run(
                    ['docker', 'load', '-i', tmp_path],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                
                # 解析输出获取镜像信息
                # docker load 的输出格式类似: "Loaded image: busybox:latest" 或 "Loaded image ID: sha256:..."
                output_lines = result.stdout.strip().split('\n')
                loaded_images = []
                loaded_image_ids = []
                
                for line in output_lines:
                    if 'Loaded image:' in line:
                        # 提取镜像名称（可能包含 tag）
                        image_name = line.split('Loaded image:')[1].strip()
                        loaded_images.append(image_name)
                    elif 'Loaded image ID:' in line:
                        # 提取镜像 ID
                        image_id = line.split('Loaded image ID:')[1].strip()
                        loaded_image_ids.append(image_id)
                
                log.info(f'导入镜像输出: {result.stdout}')
                log.info(f'解析到的镜像名称: {loaded_images}')
                log.info(f'解析到的镜像ID: {loaded_image_ids}')
                
                # 获取所有镜像列表，找到刚导入的镜像
                images = self.list_images(all=True)
                log.info(f'当前镜像列表数量: {len(images)}')
                
                # 方法1: 通过 tag 匹配
                if loaded_images:
                    for img in images:
                        if img.get('tags'):
                            for tag in img['tags']:
                                if tag in loaded_images:
                                    log.info(f'通过 tag 找到镜像: {img["id"]}, tags: {img["tags"]}')
                                    return {
                                        'id': img['id'],
                                        'tags': img['tags'],
                                    }
                
                # 方法2: 通过镜像 ID 匹配（如果导出的镜像没有 tag）
                if loaded_image_ids:
                    for img in images:
                        # 检查镜像 ID 是否匹配（比较前12位或完整 ID）
                        img_id_short = img['id']
                        for loaded_id in loaded_image_ids:
                            # 移除 sha256: 前缀（如果有）
                            loaded_id_clean = loaded_id.replace('sha256:', '')
                            # 比较完整 ID 或前12位
                            if (loaded_id_clean.startswith(img_id_short) or 
                                img_id_short.startswith(loaded_id_clean[:12])):
                                log.info(f'通过 ID 找到镜像: {img["id"]}, tags: {img.get("tags", [])}')
                                return {
                                    'id': img['id'],
                                    'tags': img.get('tags', []),
                                }
                
                # 方法3: 如果导入后立即查询，可能是最新的镜像（按创建时间排序）
                if images:
                    # 按创建时间排序，最新的在前
                    sorted_images = sorted(
                        images,
                        key=lambda x: x.get('created', '') or '',
                        reverse=True
                    )
                    # 返回最新的镜像（假设是刚导入的）
                    latest_image = sorted_images[0]
                    log.info(f'返回最新镜像: {latest_image["id"]}, tags: {latest_image.get("tags", [])}')
                    return {
                        'id': latest_image['id'],
                        'tags': latest_image.get('tags', []),
                    }
                
                # 如果都没有找到，返回解析到的镜像名称
                log.warning(f'未找到匹配的镜像，返回解析到的镜像名称: {loaded_images}')
                return {
                    'id': '',
                    'tags': loaded_images if loaded_images else [],
                }
            finally:
                # 删除临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            log.error(f'导入镜像失败: {error_msg}')
            raise DockerException(f'导入镜像失败: {error_msg}')
        except Exception as e:
            log.error(f'导入镜像失败: {e}')
            raise

    def get_image_detail(self, image_id: str) -> dict[str, Any]:
        """
        获取镜像详情，包括 Dockerfile details 和 layers

        :param image_id: 镜像ID或名称
        :return: 镜像详情
        """
        try:
            import json
            
            # 使用 inspect 获取镜像详细信息
            image = self.client.image.inspect(image_id)
            
            # 转换为字典格式
            image_dict = None
            if hasattr(image, '__dict__'):
                try:
                    image_dict = image.__dict__
                except Exception:
                    pass
            
            if image_dict is None and isinstance(image, dict):
                image_dict = image
            elif image_dict is None:
                try:
                    image_dict = json.loads(json.dumps(image, default=str))
                except Exception:
                    image_dict = {}
            
            # 获取 Config 信息
            config = image_dict.get('Config') or image_dict.get('config') or {}
            if not config and hasattr(image, 'config'):
                try:
                    config = image.config.__dict__ if hasattr(image.config, '__dict__') else {}
                except Exception:
                    pass
            
            # 提取 CMD
            cmd = config.get('Cmd') or config.get('cmd') or []
            if isinstance(cmd, str):
                cmd = [cmd]
            
            # 提取 ENTRYPOINT
            entrypoint = config.get('Entrypoint') or config.get('entrypoint') or []
            if isinstance(entrypoint, str):
                entrypoint = [entrypoint]
            
            # 提取 EXPOSE 端口
            expose = config.get('ExposedPorts') or config.get('exposed_ports') or {}
            expose_list = []
            if isinstance(expose, dict):
                expose_list = list(expose.keys())
            elif isinstance(expose, list):
                expose_list = expose
            
            # 提取 VOLUME
            volumes = config.get('Volumes') or config.get('volumes') or {}
            volume_list = []
            if isinstance(volumes, dict):
                volume_list = list(volumes.keys())
            elif isinstance(volumes, list):
                volume_list = volumes
            
            # 提取 ENV 环境变量
            env_list = config.get('Env') or config.get('env') or []
            env_dict = {}
            if isinstance(env_list, list):
                for env_item in env_list:
                    if isinstance(env_item, str) and '=' in env_item:
                        key, value = env_item.split('=', 1)
                        env_dict[key] = value
            
            # 获取镜像历史（layers）
            # 需要先获取镜像对象，然后在镜像对象上调用 history()
            history = None
            try:
                # 方法1: 尝试通过 list 找到镜像对象
                images = self.client.image.list(all=True)
                image_obj = None
                for img in images:
                    # 检查镜像 ID 是否匹配
                    if (img.id.startswith(image_id) or 
                        image_id.startswith(img.id[:12]) or
                        img.id[:12] == image_id):
                        image_obj = img
                        break
                
                if image_obj:
                    # 在镜像对象上调用 history()
                    history = image_obj.history()
            except Exception as e:
                log.warning(f'获取镜像历史失败: {e}')
                history = None
            
            layers = []
            if history:
                # 历史记录是倒序的（最新的在前），我们需要反转
                history_list = list(history)
                history_list.reverse()
                
                for index, layer in enumerate(history_list):
                    layer_dict = None
                    if hasattr(layer, '__dict__'):
                        try:
                            layer_dict = layer.__dict__
                        except Exception:
                            pass
                    
                    if layer_dict is None and isinstance(layer, dict):
                        layer_dict = layer
                    elif layer_dict is None:
                        try:
                            layer_dict = json.loads(json.dumps(layer, default=str))
                        except Exception:
                            layer_dict = {}
                    
                    # 提取层大小
                    size = layer_dict.get('Size') or layer_dict.get('size') or 0
                    if not isinstance(size, int):
                        try:
                            size = int(size)
                        except (ValueError, TypeError):
                            size = 0
                    
                    # 提取层命令 - 获取完整的 CreatedBy 字段
                    created_by = layer_dict.get('CreatedBy') or layer_dict.get('created_by') or ''
                    if not isinstance(created_by, str):
                        created_by = str(created_by) if created_by else ''
                    
                    # 如果没有 CreatedBy，尝试从其他字段获取
                    if not created_by:
                        # 尝试从 Comment 字段获取
                        comment = layer_dict.get('Comment') or layer_dict.get('comment') or ''
                        if comment:
                            created_by = comment
                    
                    # 清理和格式化层命令
                    if created_by:
                        # 移除多余的 RUN 前缀（某些情况下会有重复的 RUN）
                        created_by = created_by.strip()
                        # 保留原始格式，不做过多处理
                        pass
                    else:
                        # 如果完全没有命令信息，标记为未知
                        created_by = '<missing>'
                    
                    layers.append({
                        'order': index,
                        'size': size,
                        'layer': created_by,
                    })
            
            # 补充元数据层（从 Config 中提取的 EXPOSE, VOLUME, CMD, ENTRYPOINT）
            # 这些信息在 history 中可能不会单独显示，需要手动添加
            # 注意：这些层的大小都是 0，但需要显示在正确的位置
            
            # 如果最后几层是元数据层（CMD, ENTRYPOINT, EXPOSE, VOLUME），确保它们被包含
            # 实际上，这些信息应该已经在 history 中了，但可能需要确保格式正确
            
            # 获取镜像基本信息
            image_id_short = image_dict.get('Id') or image_dict.get('id') or image_id
            if isinstance(image_id_short, str) and len(image_id_short) > 12:
                image_id_short = image_id_short[:12]
            
            repo_tags = image_dict.get('RepoTags') or image_dict.get('repo_tags') or []
            if not isinstance(repo_tags, list):
                repo_tags = []
            
            return {
                'id': image_id_short,
                'tags': repo_tags,
                'cmd': cmd,
                'entrypoint': entrypoint,
                'expose': expose_list,
                'volume': volume_list,
                'env': env_dict,
                'layers': layers,
            }
        except DockerException as e:
            log.error(f'获取镜像详情失败: {e}')
            raise
        except Exception as e:
            log.error(f'获取镜像详情时发生未知错误: {e}')
            raise

    # ==================== 堆栈管理 (Docker Compose) ====================

    def list_stacks(self) -> list[dict[str, Any]]:
        """
        列出所有堆栈

        :return: 堆栈列表
        """
        try:
            # 直接使用subprocess执行docker compose ls命令，避免--format选项兼容性问题
            # 某些Docker版本不支持--format选项
            result = subprocess.run(
                ['docker', 'compose', 'ls'],
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                # 如果docker compose失败，尝试使用docker-compose（旧版本）
                result = subprocess.run(
                    ['docker-compose', 'ls'],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            
            if result.returncode != 0:
                log.error(f'执行docker compose ls失败: {result.stderr}')
                raise DockerException(f'执行docker compose ls失败: {result.stderr}')
            
            # 解析输出
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                # 没有堆栈或只有表头
                return []
            
            # 跳过表头行，解析数据行
            stacks = []
            for line in lines[1:]:
                if not line.strip():
                    continue
                
                # 解析格式: NAME STATUS CONFIG FILES
                # Docker Compose输出通常是固定宽度的表格，使用多个空格分隔
                # 使用正则表达式分割多个连续空格
                parts = re.split(r'\s{2,}', line.strip())
                
                if len(parts) >= 2:
                    name = parts[0]
                    status = parts[1]
                    # config_files是剩余部分（可能包含逗号分隔的多个文件）
                    config_files_str = ' '.join(parts[2:]) if len(parts) > 2 else ''
                    # 处理配置文件路径，可能用逗号分隔
                    config_files = [f.strip() for f in config_files_str.split(',') if f.strip()] if config_files_str else []
                    
                    # 获取堆栈的创建时间和更新时间（通过检查堆栈中的容器）
                    created = None
                    updated = None
                    try:
                        # 获取堆栈中的所有容器
                        containers = self.client.container.list(
                            filters={'label': f'com.docker.compose.project={name}'},
                            all=True,
                        )
                        if containers:
                            # 获取第一个容器的创建时间作为堆栈的创建时间
                            first_container = containers[0]
                            try:
                                inspected = self.client.container.inspect(first_container.id)
                                
                                # 获取创建时间
                                container_created = None
                                if hasattr(inspected, 'created'):
                                    container_created = inspected.created
                                elif isinstance(inspected, dict):
                                    container_created = inspected.get('Created') or inspected.get('created')
                                
                                if container_created:
                                    if hasattr(container_created, 'isoformat'):
                                        created = container_created.isoformat()
                                    elif isinstance(container_created, str):
                                        created = container_created
                                
                                # 获取更新时间（使用容器状态中的 StartedAt 或 State.StartedAt）
                                container_updated = None
                                if hasattr(inspected, 'State') and hasattr(inspected.State, 'StartedAt'):
                                    container_updated = inspected.State.StartedAt
                                elif isinstance(inspected, dict):
                                    state = inspected.get('State') or inspected.get('state')
                                    if state:
                                        container_updated = state.get('StartedAt') or state.get('started_at')
                                
                                if container_updated:
                                    if hasattr(container_updated, 'isoformat'):
                                        updated = container_updated.isoformat()
                                    elif isinstance(container_updated, str):
                                        updated = container_updated
                                    # 如果 updated 为空，使用 created 作为 fallback
                                    if not updated and created:
                                        updated = created
                                        
                            except Exception as e:
                                log.debug(f'获取堆栈 {name} 的创建时间和更新时间失败: {e}')
                    except Exception as e:
                        log.debug(f'获取堆栈 {name} 的容器列表失败: {e}')
                    
                    # 获取堆栈中的容器名称列表
                    container_names = []
                    try:
                        stack_containers = self.client.container.list(
                            filters={'label': f'com.docker.compose.project={name}'},
                            all=True,
                        )
                        container_names = [c.name for c in stack_containers if c.name]
                    except Exception as e:
                        log.debug(f'获取堆栈 {name} 的容器名称失败: {e}')
                    
                    stacks.append({
                        'name': name,
                        'status': status,
                        'config_files': config_files,
                        'containers': container_names,
                        'created': created,
                        'updated': updated,
                    })
            
            return stacks
        except subprocess.SubprocessError as e:
            log.error(f'执行docker compose ls命令失败: {e}')
            raise DockerException(f'执行docker compose ls命令失败: {e}')
        except Exception as e:
            log.error(f'获取堆栈列表失败: {e}')
            raise

    def deploy_stack(self, compose_file: str, project_name: str | None = None) -> dict[str, Any]:
        """
        部署堆栈（启动Docker Compose）

        :param compose_file: Compose文件路径
        :param project_name: 项目名称
        :return: 部署结果
        """
        try:
            self.client.compose.up(
                compose_files=[compose_file],
                project_name=project_name,
                detach=True,
            )
            return {'status': 'deployed', 'compose_file': compose_file}
        except DockerException as e:
            log.error(f'部署堆栈失败: {e}')
            raise

    def stop_stack(self, project_name: str, compose_file: str | None = None) -> bool:
        """
        停止堆栈

        :param project_name: 项目名称
        :param compose_file: Compose文件路径
        :return: 是否成功
        """
        try:
            self.client.compose.stop(
                project_name=project_name,
                compose_files=[compose_file] if compose_file else None,
            )
            return True
        except DockerException as e:
            log.error(f'停止堆栈失败: {e}')
            raise

    def remove_stack(self, project_name: str, compose_file: str | None = None, volumes: bool = False) -> bool:
        """
        删除堆栈

        :param project_name: 项目名称
        :param compose_file: Compose文件路径
        :param volumes: 是否同时删除卷
        :return: 是否成功
        """
        try:
            self.client.compose.down(
                project_name=project_name,
                compose_files=[compose_file] if compose_file else None,
                volumes=volumes,
            )
            return True
        except DockerException as e:
            log.error(f'删除堆栈失败: {e}')
            raise

    def get_stack_services(self, project_name: str, compose_file: str | None = None) -> list[dict[str, Any]]:
        """
        获取堆栈服务列表

        :param project_name: 项目名称
        :param compose_file: Compose文件路径
        :return: 服务列表
        """
        try:
            services = self.client.compose.ps(
                project_name=project_name,
                compose_files=[compose_file] if compose_file else None,
            )
            return [
                {
                    'name': service.name,
                    'id': service.id[:12],
                    'image': service.image,
                    'status': service.state,
                }
                for service in services
            ]
        except DockerException as e:
            log.error(f'获取堆栈服务列表失败: {e}')
            raise

    # ==================== 网络管理 ====================

    def list_networks(self) -> list[dict[str, Any]]:
        """
        列出所有网络

        :return: 网络列表
        """
        try:
            networks = self.client.network.list()
            result = []
            for network in networks:
                # 获取网络详细信息
                stack = None
                attachable = False
                ipam_driver = 'default'
                ipv4_subnet = None
                ipv4_gateway = None
                ipv6_subnet = None
                ipv6_gateway = None
                ownership = 'public'  # 默认值
                
                # 获取连接到该网络的容器列表
                containers = []
                try:
                    # 使用 inspect 获取网络详细信息
                    inspected = self.client.network.inspect(network.id)
                    
                    # 获取 containers
                    network_containers = None
                    if hasattr(inspected, 'containers') and inspected.containers:
                        network_containers = inspected.containers
                    elif hasattr(inspected, 'Containers') and inspected.Containers:
                        network_containers = inspected.Containers
                    elif isinstance(inspected, dict):
                        network_containers = inspected.get('Containers') or inspected.get('containers')
                    
                    if network_containers:
                        if isinstance(network_containers, dict):
                            # 如果是字典，键是容器ID，值是容器信息
                            for container_id, container_info in network_containers.items():
                                # 尝试获取容器名称
                                container_name = None
                                if isinstance(container_info, dict):
                                    container_name = container_info.get('Name') or container_info.get('name')
                                # 如果没有名称，尝试通过容器ID获取
                                if not container_name:
                                    try:
                                        container = self.client.container.inspect(container_id)
                                        if hasattr(container, 'name'):
                                            container_name = container.name
                                        elif isinstance(container, dict):
                                            container_name = container.get('Name') or container.get('name')
                                        # 移除名称前缀的 /
                                        if container_name and container_name.startswith('/'):
                                            container_name = container_name[1:]
                                    except Exception:
                                        container_name = container_id[:12] if len(container_id) > 12 else container_id
                                if container_name:
                                    containers.append(container_name)
                        elif isinstance(network_containers, list):
                            # 如果是列表，直接获取容器名称
                            for container in network_containers:
                                if isinstance(container, dict):
                                    container_name = container.get('Name') or container.get('name')
                                    if container_name:
                                        if container_name.startswith('/'):
                                            container_name = container_name[1:]
                                        containers.append(container_name)
                                elif hasattr(container, 'name'):
                                    container_name = container.name
                                    if container_name and container_name.startswith('/'):
                                        container_name = container_name[1:]
                                    containers.append(container_name)
                    
                    # 获取 labels
                    labels = None
                    if hasattr(inspected, 'labels') and inspected.labels:
                        labels = inspected.labels
                    elif hasattr(inspected, 'Labels') and inspected.Labels:
                        labels = inspected.Labels
                    elif isinstance(inspected, dict):
                        labels = inspected.get('Labels') or inspected.get('labels')
                    
                    if labels and isinstance(labels, dict):
                        stack = labels.get('com.docker.compose.project') or labels.get('com.docker.compose.project.working_dir')
                        if stack and '/' in stack:
                            stack = stack.split('/')[-1]
                        # 从 labels 中获取 ownership（如果有的话）
                        ownership_label = labels.get('com.docker.compose.project.ownership') or labels.get('ownership')
                        if ownership_label:
                            ownership = ownership_label
                    
                    # 获取 attachable 属性
                    if hasattr(inspected, 'attachable'):
                        attachable = inspected.attachable
                    elif isinstance(inspected, dict):
                        attachable = inspected.get('Attachable') or inspected.get('attachable') or False
                    
                    # 获取 IPAM 配置
                    ipam = None
                    if hasattr(inspected, 'ipam') and inspected.ipam:
                        ipam = inspected.ipam
                    elif isinstance(inspected, dict):
                        ipam = inspected.get('IPAM') or inspected.get('ipam')
                    
                    if ipam:
                        # 获取 IPAM driver
                        if hasattr(ipam, 'driver') and ipam.driver:
                            ipam_driver = ipam.driver
                        elif isinstance(ipam, dict):
                            ipam_driver = ipam.get('Driver') or ipam.get('driver') or 'default'
                        
                        # 获取 IPAM config
                        ipam_config = None
                        if hasattr(ipam, 'config') and ipam.config:
                            ipam_config = ipam.config
                        elif isinstance(ipam, dict):
                            ipam_config = ipam.get('Config') or ipam.get('config')
                        
                        if ipam_config:
                            # 处理 IPv4 和 IPv6 配置
                            for config in ipam_config if isinstance(ipam_config, list) else [ipam_config]:
                                config_dict = config if isinstance(config, dict) else config.__dict__ if hasattr(config, '__dict__') else {}
                                
                                subnet = config_dict.get('Subnet') or config_dict.get('subnet') or ''
                                gateway = config_dict.get('Gateway') or config_dict.get('gateway') or ''
                                
                                # 判断是 IPv4 还是 IPv6
                                if ':' in subnet or '::' in subnet:
                                    # IPv6
                                    if not ipv6_subnet:
                                        ipv6_subnet = subnet
                                    if gateway and not ipv6_gateway:
                                        ipv6_gateway = gateway
                                else:
                                    # IPv4
                                    if not ipv4_subnet:
                                        ipv4_subnet = subnet
                                    if gateway and not ipv4_gateway:
                                        ipv4_gateway = gateway
                except Exception as e:
                    log.debug(f'获取网络 {network.name} 的详细信息失败: {e}')
                
                # 如果没有从 inspect 获取到 subnet，使用原来的方式
                if not ipv4_subnet and not ipv6_subnet:
                    if hasattr(network, 'ipam') and network.ipam:
                        if hasattr(network.ipam, 'config') and network.ipam.config:
                            if len(network.ipam.config) > 0 and hasattr(network.ipam.config[0], 'subnet'):
                                subnet = network.ipam.config[0].subnet
                                if ':' in subnet or '::' in subnet:
                                    ipv6_subnet = subnet
                                else:
                                    ipv4_subnet = subnet
                
                result.append({
                    'id': network.id[:12] if len(network.id) > 12 else network.id,
                    'name': network.name,
                    'driver': network.driver if hasattr(network, 'driver') else 'bridge',
                    'scope': network.scope if hasattr(network, 'scope') else 'local',
                    'subnet': ipv4_subnet or ipv6_subnet,  # 保持向后兼容
                    'stack': stack,
                    'attachable': attachable,
                    'ipam_driver': ipam_driver,
                    'ipv4_subnet': ipv4_subnet,
                    'ipv4_gateway': ipv4_gateway,
                    'ipv6_subnet': ipv6_subnet,
                    'ipv6_gateway': ipv6_gateway,
                    'ownership': ownership,
                    'containers': containers,
                })
            return result
        except DockerException as e:
            log.error(f'获取网络列表失败: {e}')
            raise

    def create_network(
        self,
        name: str,
        driver: str = 'bridge',
        subnet: str | None = None,
        gateway: str | None = None,
    ) -> dict[str, Any]:
        """
        创建网络

        :param name: 网络名称
        :param driver: 驱动类型 (bridge, overlay, host, none)
        :param subnet: 子网
        :param gateway: 网关
        :return: 创建的网络信息
        """
        try:
            # python-on-whales 的 network.create 直接接受 subnet 和 gateway 参数
            create_kwargs = {
                'name': name,
                'driver': driver,
            }
            if subnet:
                create_kwargs['subnet'] = subnet
            if gateway:
                create_kwargs['gateway'] = gateway
            
            network = self.client.network.create(**create_kwargs)
            return {
                'id': network.id[:12],
                'name': network.name,
            }
        except DockerException as e:
            log.error(f'创建网络失败: {e}')
            raise

    def remove_network(self, network_id: str) -> bool:
        """
        删除网络

        :param network_id: 网络ID或名称
        :return: 是否成功
        """
        try:
            self.client.network.remove(network_id)
            return True
        except DockerException as e:
            log.error(f'删除网络失败: {e}')
            raise

    # ==================== 卷管理 ====================

    def list_volumes(self) -> list[dict[str, Any]]:
        """
        列出所有卷

        :return: 卷列表
        """
        try:
            volumes = self.client.volume.list()
            result = []
            for volume in volumes:
                mountpoint = volume.mountpoint if hasattr(volume, 'mountpoint') else ''
                # 将 PosixPath 转换为字符串
                mountpoint = str(mountpoint) if mountpoint else ''
                
                # 获取卷的详细信息（包含 labels 和 options）
                stack = None
                volume_options = {}
                try:
                    # 使用 inspect 获取卷的详细信息
                    try:
                        inspected = self.client.volume.inspect(volume.name)
                        
                        # 获取 labels
                        labels = None
                        if hasattr(inspected, 'labels') and inspected.labels:
                            labels = inspected.labels
                        elif hasattr(inspected, 'Labels') and inspected.Labels:
                            labels = inspected.Labels
                        elif isinstance(inspected, dict):
                            labels = inspected.get('Labels') or inspected.get('labels')
                        
                        if labels and isinstance(labels, dict):
                            stack = labels.get('com.docker.compose.project') or labels.get('com.docker.compose.project.working_dir')
                            if stack and '/' in stack:
                                stack = stack.split('/')[-1]
                        
                        # 获取 options
                        if hasattr(inspected, 'options') and inspected.options:
                            if isinstance(inspected.options, dict):
                                volume_options = inspected.options
                            else:
                                try:
                                    volume_options = dict(inspected.options) if inspected.options else {}
                                except Exception:
                                    volume_options = {}
                    except Exception as e:
                        log.debug(f'检查卷 {volume.name} 的详细信息失败: {e}')
                except Exception as e:
                    log.debug(f'获取卷 {volume.name} 的详细信息失败: {e}')
                    stack = None
                
                # 获取使用该卷的容器名称列表
                containers_using_volume = []
                try:
                    all_containers = self.client.container.list(all=True)
                    for container in all_containers:
                        try:
                            inspected = self.client.container.inspect(container.id)
                            inspected_dict = None
                            
                            # 转换为字典
                            if hasattr(inspected, '__dict__'):
                                try:
                                    inspected_dict = inspected.__dict__
                                except Exception:
                                    pass
                            if inspected_dict is None and isinstance(inspected, dict):
                                inspected_dict = inspected
                            elif inspected_dict is None:
                                try:
                                    import json
                                    inspected_dict = json.loads(json.dumps(inspected, default=str))
                                except Exception:
                                    pass
                            
                            # 检查容器的挂载点
                            # 首先尝试使用 container.mounts 属性（python-on-whales 的方式）
                            try:
                                if hasattr(container, 'mounts') and container.mounts:
                                    for mount in container.mounts:
                                        if hasattr(mount, 'type') and mount.type == 'volume':
                                            mount_name = getattr(mount, 'name', None)
                                            if mount_name == volume.name:
                                                containers_using_volume.append(container.name)
                                                break
                            except Exception:
                                pass
                            
                            # 如果上面没有找到，尝试从 inspected_dict 中查找
                            if volume.name not in containers_using_volume and inspected_dict:
                                mounts = inspected_dict.get('Mounts') or inspected_dict.get('mounts')
                                if mounts and isinstance(mounts, list):
                                    for mount in mounts:
                                        if isinstance(mount, dict):
                                            mount_type = mount.get('Type') or mount.get('type') or ''
                                            # 对于 volume 类型，使用 Name 字段匹配卷名称
                                            mount_name = mount.get('Name') or mount.get('name') or ''
                                            # 如果 Name 不存在，尝试从 Source 中提取卷名称
                                            if not mount_name:
                                                source = mount.get('Source') or mount.get('source') or ''
                                                # Source 格式通常是 /var/lib/docker/volumes/volume_name/_data
                                                if '/volumes/' in source:
                                                    parts = source.split('/volumes/')
                                                    if len(parts) > 1:
                                                        mount_name = parts[1].split('/')[0]
                                            
                                            if mount_type == 'volume' and mount_name == volume.name:
                                                containers_using_volume.append(container.name)
                                                break
                        except Exception as e:
                            log.debug(f'检查容器 {container.id} 的卷挂载失败: {e}')
                            continue
                except Exception as e:
                    log.debug(f'获取使用卷 {volume.name} 的容器列表失败: {e}')
                
                result.append({
                    'name': volume.name,
                    'driver': volume.driver if hasattr(volume, 'driver') else 'local',
                    'mountpoint': mountpoint,
                    'created': volume.created_at.isoformat() if hasattr(volume, 'created_at') and volume.created_at else None,
                    'stack': stack,
                    'options': volume_options,
                    'containers': containers_using_volume,
                })
            return result
        except DockerException as e:
            log.error(f'获取卷列表失败: {e}')
            raise

    def create_volume(self, name: str, driver: str = 'local', driver_opts: dict[str, str] | None = None) -> dict[str, Any]:
        """
        创建卷

        :param name: 卷名称
        :param driver: 驱动类型
        :param driver_opts: 驱动选项
        :return: 创建的卷信息
        """
        try:
            volume = self.client.volume.create(
                volume_name=name,
                driver=driver,
                options=driver_opts or {}
            )
            return {
                'name': volume.name,
                'driver': volume.driver,
            }
        except DockerException as e:
            log.error(f'创建卷失败: {e}')
            raise

    def get_volume_detail(self, volume_name: str) -> dict[str, Any]:
        """
        获取卷详情和使用该卷的容器列表

        :param volume_name: 卷名称
        :return: 卷详情，包括选项和使用该卷的容器列表
        """
        try:
            # 获取卷的详细信息
            volume = self.client.volume.inspect(volume_name)
            
            # 获取卷的选项（driver options）
            volume_options = {}
            if hasattr(volume, 'options') and volume.options:
                # 确保 options 是字典类型
                if isinstance(volume.options, dict):
                    volume_options = volume.options
                else:
                    # 如果不是字典，尝试转换
                    try:
                        volume_options = dict(volume.options) if volume.options else {}
                    except Exception:
                        volume_options = {}
            elif hasattr(volume, 'Options') and volume.Options:
                if isinstance(volume.Options, dict):
                    volume_options = volume.Options
                else:
                    try:
                        volume_options = dict(volume.Options) if volume.Options else {}
                    except Exception:
                        volume_options = {}
            elif isinstance(volume, dict):
                volume_options = volume.get('Options') or volume.get('options') or {}
                if not isinstance(volume_options, dict):
                    volume_options = {}
            
            # 获取所有容器，查找使用该卷的容器
            containers_using_volume = []
            try:
                all_containers = self.client.container.list(all=True)
                for container in all_containers:
                    try:
                        inspected = self.client.container.inspect(container.id)
                        inspected_dict = None
                        
                        # 转换为字典
                        if hasattr(inspected, '__dict__'):
                            try:
                                inspected_dict = inspected.__dict__
                            except Exception:
                                pass
                        if inspected_dict is None and isinstance(inspected, dict):
                            inspected_dict = inspected
                        elif inspected_dict is None:
                            try:
                                import json
                                inspected_dict = json.loads(json.dumps(inspected, default=str))
                            except Exception:
                                pass
                        
                        # 检查容器的挂载点
                        if inspected_dict:
                            mounts = inspected_dict.get('Mounts') or inspected_dict.get('mounts')
                            if mounts and isinstance(mounts, list):
                                for mount in mounts:
                                    if isinstance(mount, dict):
                                        # 检查是否是卷挂载
                                        mount_type = mount.get('Type') or mount.get('type') or ''
                                        source = mount.get('Source') or mount.get('source') or mount.get('Name') or mount.get('name') or ''
                                        
                                        # 如果是卷类型，且卷名称匹配
                                        if mount_type == 'volume' and source == volume_name:
                                            destination = mount.get('Destination') or mount.get('destination') or ''
                                            read_only = mount.get('ReadOnly') or mount.get('read_only') or mount.get('RW') is False
                                            
                                            containers_using_volume.append({
                                                'name': container.name,
                                                'mounted_at': destination,
                                                'read_only': bool(read_only),
                                            })
                                            break
                    except Exception as e:
                        log.debug(f'检查容器 {container.id} 的卷挂载失败: {e}')
                        continue
            except Exception as e:
                log.warning(f'获取使用卷 {volume_name} 的容器列表失败: {e}')
            
            return {
                'options': volume_options,
                'containers': containers_using_volume,
            }
        except DockerException as e:
            log.error(f'获取卷详情失败: {e}')
            raise

    def remove_volume(self, volume_name: str) -> bool:
        """
        删除卷

        :param volume_name: 卷名称
        :return: 是否成功
        """
        try:
            self.client.volume.remove(volume_name)
            return True
        except DockerException as e:
            log.error(f'删除卷失败: {e}')
            raise

    # ==================== 系统信息 ====================

    def get_system_info(self) -> dict[str, Any]:
        """
        获取Docker系统信息

        :return: 系统信息
        """
        try:
            info = self.client.info()
            # 尝试多种方式获取 CPU 数量（Docker API 可能使用 NCPU、n_cpu 或 cpus）
            cpus = (
                getattr(info, 'NCPU', None) or
                getattr(info, 'n_cpu', None) or
                getattr(info, 'cpus', None) or
                0
            )
            # 如果获取到的是 None，转换为 0
            if cpus is None:
                cpus = 0
            # 宿主总内存（字节），Docker API 可能为 MemTotal 或 mem_total；info 可能是 dict 或对象
            if isinstance(info, dict):
                mem_total = info.get('MemTotal') or info.get('mem_total') or 0
            else:
                mem_total = (
                    getattr(info, 'MemTotal', None) or
                    getattr(info, 'mem_total', None) or
                    0
                )
            if mem_total is None:
                mem_total = 0

            return {
                'containers': getattr(info, 'containers', 0),
                'containers_running': getattr(info, 'containers_running', 0),
                'containers_paused': getattr(info, 'containers_paused', 0),
                'containers_stopped': getattr(info, 'containers_stopped', 0),
                'images': getattr(info, 'images', 0),
                'driver': getattr(info, 'driver', ''),
                'memory_limit': getattr(info, 'memory_limit', False),
                'mem_total': int(mem_total) if mem_total else 0,
                'cpus': int(cpus) if cpus else 0,
                'kernel_version': getattr(info, 'kernel_version', ''),
                'operating_system': getattr(info, 'operating_system', ''),
                'os_type': getattr(info, 'os_type', ''),
                'architecture': getattr(info, 'architecture', ''),
                'docker_version': getattr(info, 'server_version', ''),
            }
        except DockerException as e:
            log.error(f'获取Docker系统信息失败: {e}')
            raise

    def get_disk_usage(self) -> dict[str, Any]:
        """
        获取Docker磁盘使用情况

        :return: 磁盘使用情况
        """
        try:
            # 使用 subprocess 执行 docker system df 命令
            result = subprocess.run(
                ['docker', 'system', 'df'],
                capture_output=True,
                text=True,
                check=True,
            )
            
            # 解析文本输出
            lines = result.stdout.strip().split('\n')
            
            images_size = 0
            containers_size = 0
            volumes_size = 0
            build_cache_size = 0
            
            # 跳过表头，解析数据行
            # 格式示例:
            # TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
            # Images          5         3         1.2GB     800MB (66%)
            # Containers      3         2         500MB     200MB (40%)
            # Local Volumes   2         1         300MB     100MB (33%)
            # Build Cache     0         0         0B        0B
            for line in lines[1:]:  # 跳过表头
                if not line.strip():
                    continue
                
                # 使用正则表达式分割多个空格
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) >= 4:
                    resource_type = parts[0].lower()
                    size_str = parts[3]  # SIZE 列
                    
                    # 解析大小字符串（如 "1.2GB", "500MB"）
                    size_bytes = self._parse_size(size_str)
                    
                    if 'image' in resource_type:
                        images_size = size_bytes
                    elif 'container' in resource_type:
                        containers_size = size_bytes
                    elif 'volume' in resource_type:
                        volumes_size = size_bytes
                    elif 'build cache' in resource_type or 'cache' in resource_type:
                        build_cache_size = size_bytes
            
            return {
                'images_size': images_size,
                'containers_size': containers_size,
                'volumes_size': volumes_size,
                'build_cache_size': build_cache_size,
                'total_size': images_size + containers_size + volumes_size + build_cache_size,
            }
        except subprocess.SubprocessError as e:
            log.error(f'执行docker system df命令失败: {e}')
            raise DockerException(f'执行docker system df命令失败: {e}')
        except Exception as e:
            log.error(f'获取Docker磁盘使用情况失败: {e}')
            raise

    # ==================== 配置管理 ====================

    @staticmethod
    async def get_connected_status(db: AsyncSession) -> bool:
        """
        获取连接状态

        :param db: 数据库会话
        :return: 连接状态
        """
        try:
            result = await db.execute(
                select(DockerConfig).where(DockerConfig.key == 'connected')
            )
            config = result.scalar_one_or_none()
            if config:
                return config.value.lower() == 'true'
            # 默认返回 False
            return False
        except Exception as e:
            log.error(f'获取连接状态失败: {e}')
            return False

    @staticmethod
    async def set_connected_status(db: AsyncSession, connected: bool) -> bool:
        """
        设置连接状态

        :param db: 数据库会话
        :param connected: 连接状态
        :return: 是否成功
        """
        try:
            result = await db.execute(
                select(DockerConfig).where(DockerConfig.key == 'connected')
            )
            config = result.scalar_one_or_none()
            
            if config:
                # 更新现有配置
                config.value = 'true' if connected else 'false'
            else:
                # 创建新配置
                config = DockerConfig(
                    key='connected',
                    value='true' if connected else 'false'
                )
                db.add(config)
            
            await db.commit()
            await db.refresh(config)
            return True
        except Exception as e:
            log.error(f'设置连接状态失败: {e}')
            await db.rollback()
            return False


# 创建单例
docker_service = DockerService()

