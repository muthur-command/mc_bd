# Docker管理插件

这是一个用于管理Docker容器、镜像、堆栈、网络、卷和系统信息的插件。

## 功能特性

### 容器管理
- 列出所有容器（支持过滤已停止的容器）
- 获取容器详情
- 创建容器
- 启动/停止/重启容器
- 删除容器
- 查看容器日志

### 镜像管理
- 列出所有镜像
- 拉取镜像
- 删除镜像
- 构建镜像

### 堆栈管理（Docker Compose）
- 列出所有堆栈
- 部署堆栈（启动Docker Compose）
- 停止堆栈
- 删除堆栈
- 获取堆栈服务列表

### 网络管理
- 列出所有网络
- 创建网络
- 删除网络

### 卷管理
- 列出所有卷
- 创建卷
- 删除卷

### 系统信息
- 获取Docker系统信息（容器数、镜像数、CPU、内存等）
- 获取Docker磁盘使用情况

## 依赖

- `python-on-whales`: Docker操作的Python客户端库

## API端点

所有API端点都需要JWT认证。

### 容器管理
- `GET /api/v1/docker/containers` - 获取容器列表
- `GET /api/v1/docker/containers/{container_id}` - 获取容器详情
- `POST /api/v1/docker/containers` - 创建容器
- `POST /api/v1/docker/containers/{container_id}/start` - 启动容器
- `POST /api/v1/docker/containers/{container_id}/stop` - 停止容器
- `POST /api/v1/docker/containers/{container_id}/restart` - 重启容器
- `DELETE /api/v1/docker/containers/{container_id}` - 删除容器
- `GET /api/v1/docker/containers/{container_id}/logs` - 获取容器日志
- `WS /api/v1/docker/containers/{container_id}/stats` - 实时获取容器统计信息（WebSocket）

### 镜像管理
- `GET /api/v1/docker/images` - 获取镜像列表
- `POST /api/v1/docker/images/pull` - 拉取镜像
- `DELETE /api/v1/docker/images/{image_id}` - 删除镜像
- `POST /api/v1/docker/images/build` - 构建镜像

### 堆栈管理
- `GET /api/v1/docker/stacks` - 获取堆栈列表
- `POST /api/v1/docker/stacks/deploy` - 部署堆栈
- `POST /api/v1/docker/stacks/stop` - 停止堆栈
- `DELETE /api/v1/docker/stacks/remove` - 删除堆栈
- `GET /api/v1/docker/stacks/services` - 获取堆栈服务列表

### 网络管理
- `GET /api/v1/docker/networks` - 获取网络列表
- `POST /api/v1/docker/networks` - 创建网络
- `DELETE /api/v1/docker/networks/{network_id}` - 删除网络

### 卷管理
- `GET /api/v1/docker/volumes` - 获取卷列表
- `POST /api/v1/docker/volumes` - 创建卷
- `DELETE /api/v1/docker/volumes/{volume_name}` - 删除卷

### 系统信息
- `GET /api/v1/docker/system/info` - 获取Docker系统信息
- `GET /api/v1/docker/system/df` - 获取Docker磁盘使用情况

## 使用示例

### WebSocket实时监控容器资源使用情况

通过WebSocket连接可以实时获取容器的CPU、内存、网络和I/O使用情况：

```javascript
// 前端JavaScript示例
const containerId = 'your_container_id';
const ws = new WebSocket(`ws://your_backend_url/api/v1/docker/containers/${containerId}/stats`);

ws.onopen = function() {
    console.log('WebSocket连接已建立');
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    if (message.type === 'stats') {
        const stats = message.data;
        console.log('CPU使用率:', stats.cpu_percent + '%');
        console.log('内存使用:', (stats.memory_usage / 1024 / 1024).toFixed(2) + 'MB');
        console.log('内存使用率:', stats.memory_percent + '%');
        console.log('网络接收:', (stats.network_rx / 1024 / 1024).toFixed(2) + 'MB');
        console.log('网络发送:', (stats.network_tx / 1024 / 1024).toFixed(2) + 'MB');
        console.log('I/O读取:', (stats.io_read / 1024 / 1024).toFixed(2) + 'MB');
        console.log('I/O写入:', (stats.io_write / 1024 / 1024).toFixed(2) + 'MB');
        
        // 更新前端界面
        updateStatsDisplay(stats);
    } else if (message.type === 'error') {
        console.error('错误:', message.message);
    }
};

ws.onclose = function(event) {
    console.log('WebSocket连接已关闭');
};

ws.onerror = function(error) {
    console.error('WebSocket错误:', error);
};
```

**WebSocket消息格式：**

- 正常统计信息：
```json
{
  "type": "stats",
  "data": {
    "cpu_percent": 25.5,
    "memory_usage": 52428800,
    "memory_limit": 1073741824,
    "memory_percent": 4.88,
    "network_rx": 1024000,
    "network_tx": 512000,
    "io_read": 2048000,
    "io_write": 1024000,
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

- 错误信息：
```json
{
  "type": "error",
  "message": "错误描述"
}
```

### 创建容器
```json
POST /api/v1/docker/containers
{
  "image": "nginx:latest",
  "name": "my-nginx",
  "ports": {
    "80": (0, 8080)
  },
  "restart_policy": "always"
}
```

### 拉取镜像
```json
POST /api/v1/docker/images/pull
{
  "image": "ubuntu",
  "tag": "20.04"
}
```

### 部署堆栈
```json
POST /api/v1/docker/stacks/deploy
{
  "compose_file": "/path/to/docker-compose.yml",
  "project_name": "my-project"
}
```

## 前端菜单配置

由于系统菜单是从数据库加载的，需要在数据库中添加菜单项才能在前端显示。

### 使用 SQL 脚本（推荐）

执行对应数据库类型的 SQL 脚本：

```bash
# MySQL/MariaDB
mysql -u your_user -p your_database < sql/mysql/init.sql

# PostgreSQL
psql -U your_user -d your_database -f sql/postgresql/init.sql
```

SQL 脚本会自动创建以下菜单项：
- Container（主菜单，目录类型）
  - 仪表板
  - 容器
  - 镜像
  - 网络
  - 卷
  - 堆栈

### 手动配置

也可以通过系统管理界面的"菜单配置"功能手动添加菜单项。详细配置说明请参考前端插件的 README.md。

## 注意事项

1. 确保Docker守护进程正在运行
2. 确保运行插件的用户有权限访问Docker（通常需要加入docker组）
3. 某些操作（如删除容器、镜像）可能需要谨慎使用，建议在生产环境中添加额外的权限控制
4. 前端菜单配置需要在数据库中执行 SQL 脚本或手动添加菜单项
