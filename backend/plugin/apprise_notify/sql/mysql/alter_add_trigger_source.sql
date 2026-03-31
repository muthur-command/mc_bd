-- 已有库升级：为发送历史增加触发来源字段（新装可忽略，init.sql 已含该列）
ALTER TABLE `plugin_apprise_notify_log`
  ADD COLUMN `trigger_source` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '触发来源 test/notify' AFTER `error_message`;
