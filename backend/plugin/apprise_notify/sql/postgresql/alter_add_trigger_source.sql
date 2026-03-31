-- 已有库升级：为发送历史增加触发来源字段（新装可忽略，init.sql 已含该列）
ALTER TABLE plugin_apprise_notify_log
  ADD COLUMN IF NOT EXISTS trigger_source VARCHAR(32) NOT NULL DEFAULT '';

COMMENT ON COLUMN plugin_apprise_notify_log.trigger_source IS '触发来源：test=通道测试 notify=通知接口';
