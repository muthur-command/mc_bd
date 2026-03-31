# 系统监控插件 (system_monitor)

服务器与 Redis 监控接口由 `backend.app.admin.api.v1.monitor` 迁移至此插件。

- **路由**：`GET /api/v1/monitors/server`、`GET /api/v1/monitors/redis`（由插件挂载，需启用插件）
- **依赖**：`psutil`、`backend.database.redis`、`backend.utils.format`、`backend.utils.timezone`
- **鉴权**：两接口均使用 `DependsJwtAuth`，与原有行为一致
- **配置**：`plugin.toml` 中 `install_sidebar_group = 'Dashboards'`，与前端侧栏「System」对应

会话监控（在线用户）仍保留在 admin：`/api/v1/monitors/sessions`。
