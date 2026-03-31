# Apprise 通知插件

- 后端：`/v1/apprise-notify/*`，依赖 [Apprise](https://github.com/caronc/apprise) 实际投递。
- 通道表存储 **Apprise URL**（含密钥），请限制后台访问权限并做好备份策略。
- 前端：`mc_fd` 插件 `apprise_notify`，路径 `/plugin/apprise-notify`。

常见 URL 示例见 [Apprise 文档](https://github.com/caronc/apprise/wiki)。

## 已有数据库升级

若表 `plugin_apprise_notify_log` 已存在且缺少 `trigger_source` 列，请执行对应方言脚本：

- PostgreSQL：`sql/postgresql/alter_add_trigger_source.sql`
- MySQL：`sql/mysql/alter_add_trigger_source.sql`
