-- Apprise 通知插件（PostgreSQL）

CREATE TABLE IF NOT EXISTS plugin_apprise_notify_channel (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  apprise_url TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  description VARCHAR(512),
  created_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_time TIMESTAMPTZ
);

COMMENT ON TABLE plugin_apprise_notify_channel IS 'Apprise 通知通道';

CREATE TABLE IF NOT EXISTS plugin_apprise_notify_log (
  id BIGSERIAL PRIMARY KEY,
  channel_id BIGINT,
  channel_name VARCHAR(128) NOT NULL DEFAULT '',
  title VARCHAR(255) NOT NULL DEFAULT '',
  body TEXT NOT NULL DEFAULT '',
  status VARCHAR(32) NOT NULL,
  error_message TEXT,
  trigger_source VARCHAR(32) NOT NULL DEFAULT '',
  created_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_time TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_plugin_apprise_notify_log_channel_id ON plugin_apprise_notify_log (channel_id);

COMMENT ON TABLE plugin_apprise_notify_log IS 'Apprise 通知发送历史';
