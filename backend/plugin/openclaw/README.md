# OpenClaw 网关控制插件

在 mc_fd 中替代 OpenClaw 内置 Control UI，通过本插件获取 Gateway 地址并连接 WebSocket。

## 配置

在 `plugin.toml` 的 `[settings]` 中设置：

- `OPENCLAW_GATEWAY_BASE_URL`：Gateway 的 HTTP 地址（如 `http://localhost:18789` 或 `https://gateway.example.com`）。前端将据此推导 WebSocket 地址（`ws://` / `wss://`）。

## API

- `GET /api/v1/openclaw/config`：返回 `{ baseUrl, wsUrl }`，供 mc_fd 前端连接 Gateway WebSocket。

## 运行 OpenClaw 且禁用 Control UI

在 Docker 中运行 openclaw-cn 时，在配置中设置 `gateway.controlUi.enabled: false`，并挂载该配置文件。详见项目文档 `test/openclaw_plugin_full_plan.md`。
