"""Docker管理相关的Schema"""

from typing import Any

from pydantic import BaseModel, Field

# ==================== 容器管理 ====================


class ContainerListResponse(BaseModel):
    """容器列表响应"""

    id: str = Field(description='容器ID')
    name: str = Field(description='容器名称')
    image: str = Field(description='镜像名称')
    status: str = Field(description='状态')
    created: str | None = Field(description='创建时间')
    ports: list[str] = Field(description='端口映射')
    stack: str | None = Field(None, description='堆栈名称')
    ip_address: str | None = Field(None, description='IP地址')
    ownership: str | None = Field(None, description='所有权')


class ContainerDetailResponse(BaseModel):
    """容器详情响应"""

    id: str = Field(description='容器ID')
    name: str = Field(description='容器名称')
    image: str = Field(description='镜像名称')
    status: str = Field(description='状态')
    created: str | None = Field(description='创建时间')
    ports: dict[str, Any] = Field(description='端口映射')
    env: list[str] = Field(description='环境变量')
    command: list[str] | None = Field(description='启动命令')
    working_dir: str | None = Field(description='工作目录')
    ip_address: str | None = Field(None, description='IP地址')
    started_at: str | None = Field(None, description='启动时间')
    running_for: str | None = Field(None, description='运行时长')
    entrypoint: list[str] | None = Field(None, description='入口点')
    labels: dict[str, str] = Field(default_factory=dict, description='标签')
    restart_policy: str = Field('no', description='重启策略')
    port_configuration: list[str] = Field(default_factory=list, description='端口配置')
    volumes: list[dict[str, str]] = Field(default_factory=list, description='卷列表')
    networks: list[dict[str, str]] = Field(default_factory=list, description='网络列表')


class CreateContainerParam(BaseModel):
    """创建容器参数"""

    image: str = Field(description='镜像名称')
    name: str | None = Field(None, description='容器名称')
    command: list[str] | None = Field(None, description='启动命令')
    entrypoint: list[str] | None = Field(None, description='入口点')
    working_dir: str | None = Field(None, description='工作目录')
    user: str | None = Field(None, description='运行用户')
    env: dict[str, str] | None = Field(None, description='环境变量')
    ports: dict[str, tuple[int, int]] | None = Field(None, description='端口映射')
    publish_all_ports: bool = Field(False, description='是否发布所有暴露的端口到随机主机端口')
    volumes: dict[str, dict[str, str]] | None = Field(None, description='卷映射')
    networks: list[str] | None = Field(None, description='网络列表')
    restart_policy: str = Field('no', description='重启策略')
    labels: dict[str, str] | None = Field(None, description='标签')
    tty: bool = Field(True, description='是否分配伪终端')
    stdin_open: bool = Field(True, description='是否保持标准输入打开')
    auto_remove: bool = Field(False, description='容器退出时自动删除')
    pull_image: bool = Field(False, description='是否在创建前拉取镜像')
    registry: str | None = Field(None, description='镜像源ID')


class ContainerLogsParam(BaseModel):
    """容器日志参数"""

    tail: int = Field(100, description='显示最后N行')
    follow: bool = Field(False, description='是否持续跟踪')


class ContainerStatsResponse(BaseModel):
    """容器统计信息响应"""

    cpu_percent: float = Field(description='CPU使用率（百分比）')
    memory_usage: int = Field(description='内存使用量（字节）')
    memory_limit: int = Field(description='内存限制（字节）')
    memory_percent: float = Field(description='内存使用率（百分比）')
    network_rx: int = Field(description='网络接收字节数')
    network_tx: int = Field(description='网络发送字节数')
    io_read: int = Field(description='I/O读取字节数')
    io_write: int = Field(description='I/O写入字节数')
    timestamp: str | None = Field(None, description='时间戳')


# ==================== 镜像管理 ====================


class ImageListResponse(BaseModel):
    """镜像列表响应"""

    id: str = Field(description='镜像ID')
    tags: list[str] = Field(description='标签列表')
    size: int = Field(description='大小（字节）')
    created: str | None = Field(description='创建时间')


class ImageLayerResponse(BaseModel):
    """镜像层响应"""

    order: int = Field(description='层顺序')
    size: int = Field(description='层大小（字节）')
    layer: str = Field(description='层命令')


class ImageDetailResponse(BaseModel):
    """镜像详情响应"""

    id: str = Field(description='镜像ID')
    tags: list[str] = Field(description='标签列表')
    cmd: list[str] | None = Field(None, description='CMD命令')
    entrypoint: list[str] | None = Field(None, description='ENTRYPOINT命令')
    expose: list[str] = Field(default_factory=list, description='暴露的端口')
    volume: list[str] = Field(default_factory=list, description='卷列表')
    env: dict[str, str] = Field(default_factory=dict, description='环境变量')
    layers: list[ImageLayerResponse] = Field(default_factory=list, description='镜像层列表')


class PullImageParam(BaseModel):
    """拉取镜像参数"""

    image: str = Field(description='镜像名称')
    tag: str = Field('latest', description='标签')


class BuildImageParam(BaseModel):
    """构建镜像参数"""

    path: str = Field(description='构建上下文路径')
    tag: str = Field(description='镜像标签')
    dockerfile: str = Field('Dockerfile', description='Dockerfile路径')
    build_args: dict[str, str] | None = Field(None, description='构建参数')


# ==================== 堆栈管理 ====================


class StackListResponse(BaseModel):
    """堆栈列表响应"""

    name: str = Field(description='堆栈名称')
    status: str = Field(description='状态')
    config_files: list[str] = Field(description='配置文件列表')
    containers: list[str] = Field(default_factory=list, description='容器列表')
    created: str | None = Field(None, description='创建时间')
    updated: str | None = Field(None, description='更新时间')


class DeployStackParam(BaseModel):
    """部署堆栈参数"""

    compose_file: str = Field(description='Compose文件路径')
    project_name: str | None = Field(None, description='项目名称')


class StopStackParam(BaseModel):
    """停止堆栈参数"""

    project_name: str = Field(description='项目名称')
    compose_file: str | None = Field(None, description='Compose文件路径')


class RemoveStackParam(BaseModel):
    """删除堆栈参数"""

    project_name: str = Field(description='项目名称')
    compose_file: str | None = Field(None, description='Compose文件路径')
    volumes: bool = Field(False, description='是否同时删除卷')


class StackServicesParam(BaseModel):
    """堆栈服务列表参数"""

    project_name: str = Field(description='项目名称')
    compose_file: str | None = Field(None, description='Compose文件路径')


# ==================== 网络管理 ====================


class NetworkListResponse(BaseModel):
    """网络列表响应"""

    id: str = Field(description='网络ID')
    name: str = Field(description='网络名称')
    driver: str = Field(description='驱动类型')
    scope: str = Field(description='作用域')
    subnet: str | None = Field(None, description='子网')
    stack: str | None = Field(None, description='堆栈名称')
    attachable: bool = Field(False, description='是否可附加')
    ipam_driver: str | None = Field(None, description='IPAM驱动')
    ipv4_subnet: str | None = Field(None, description='IPv4子网')
    ipv4_gateway: str | None = Field(None, description='IPv4网关')
    ipv6_subnet: str | None = Field(None, description='IPv6子网')
    ipv6_gateway: str | None = Field(None, description='IPv6网关')
    ownership: str | None = Field(None, description='所有权')
    containers: list[str] = Field(default_factory=list, description='连接的容器列表')


class CreateNetworkParam(BaseModel):
    """创建网络参数"""

    name: str = Field(description='网络名称')
    driver: str = Field('bridge', description='驱动类型')
    subnet: str | None = Field(None, description='子网')
    gateway: str | None = Field(None, description='网关')


# ==================== 卷管理 ====================


class VolumeListResponse(BaseModel):
    """卷列表响应"""

    name: str = Field(description='卷名称')
    driver: str = Field(description='驱动类型')
    mountpoint: str = Field(description='挂载点')
    created: str | None = Field(description='创建时间')
    stack: str | None = Field(None, description='堆栈名称')
    options: dict[str, str] = Field(default_factory=dict, description='卷选项')
    containers: list[str] = Field(default_factory=list, description='使用该卷的容器名称列表')


class CreateVolumeParam(BaseModel):
    """创建卷参数"""

    name: str = Field(description='卷名称')
    driver: str = Field('local', description='驱动类型')
    driver_opts: dict[str, str] | None = Field(None, description='驱动选项')


# ==================== 系统信息 ====================


class SystemInfoResponse(BaseModel):
    """系统信息响应"""

    containers: int = Field(description='容器总数')
    containers_running: int = Field(description='运行中容器数')
    containers_paused: int = Field(description='暂停容器数')
    containers_stopped: int = Field(description='停止容器数')
    images: int = Field(description='镜像总数')
    driver: str = Field(description='存储驱动')
    memory_limit: bool = Field(description='是否限制内存')
    mem_total: int = Field(0, description='宿主总内存（字节），0 表示未获取到')
    cpus: int = Field(description='CPU数量')
    kernel_version: str = Field(description='内核版本')
    operating_system: str = Field(description='操作系统')
    os_type: str = Field(description='OS类型')
    architecture: str = Field(description='架构')
    docker_version: str = Field(description='Docker版本')


class DiskUsageResponse(BaseModel):
    """磁盘使用情况响应"""

    images_size: int = Field(description='镜像大小（字节）')
    containers_size: int = Field(description='容器大小（字节）')
    volumes_size: int = Field(description='卷大小（字节）')
    build_cache_size: int = Field(description='构建缓存大小（字节）')
    total_size: int = Field(description='总大小（字节）')


class ConnectedStatusResponse(BaseModel):
    """连接状态响应"""

    connected: bool = Field(description='连接状态')


class SetConnectedStatusParam(BaseModel):
    """设置连接状态参数"""

    connected: bool = Field(description='连接状态')


# ==================== 镜像源管理 ====================


class RegistrySourceResponse(BaseModel):
    """镜像源响应"""

    id: str = Field(description='镜像源ID')
    name: str = Field(description='镜像源名称')
    url: str = Field(description='镜像源URL')
    is_default: bool = Field(False, description='是否为默认镜像源')


class CreateRegistrySourceParam(BaseModel):
    """创建镜像源参数"""

    name: str = Field(description='镜像源名称')
    url: str = Field(description='镜像源URL')


class UpdateRegistrySourceParam(BaseModel):
    """更新镜像源参数"""

    name: str | None = Field(None, description='镜像源名称')
    url: str | None = Field(None, description='镜像源URL')
