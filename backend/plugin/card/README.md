# 卡片管理插件（后端）

- **位置**：`backend/plugin/card/`
- **API**：`GET /api/v1/cards`（需登录，当前返回空列表）
- **前端**：shadcn-vue-admin 插件 `src/plugin/card`，页面 `/plugin/card`

## 目录

- `plugin.toml` - 插件配置
- `api/router.py` - 路由挂载（v1 prefix `/api/v1/cards`）
- `api/v1/card.py` - 卡片列表接口
