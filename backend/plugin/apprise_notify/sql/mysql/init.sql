-- Apprise 通知插件（MySQL）
-- 与 backend.plugin.apprise_notify.model.apprise_notify 一致

CREATE TABLE IF NOT EXISTS `plugin_apprise_notify_channel` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `name` VARCHAR(128) NOT NULL COMMENT '显示名称',
  `apprise_url` LONGTEXT NOT NULL COMMENT 'Apprise URL',
  `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `description` VARCHAR(512) DEFAULT NULL COMMENT '备注',
  `created_time` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `updated_time` DATETIME(6) DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Apprise 通知通道';

CREATE TABLE IF NOT EXISTS `plugin_apprise_notify_log` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `channel_id` BIGINT DEFAULT NULL COMMENT '通道 ID',
  `channel_name` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '发送时通道名快照',
  `title` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '标题',
  `body` LONGTEXT NOT NULL DEFAULT '' COMMENT '正文',
  `status` VARCHAR(32) NOT NULL COMMENT 'success 或 failed',
  `error_message` LONGTEXT DEFAULT NULL COMMENT '失败原因',
  `trigger_source` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '触发来源 test/notify',
  `created_time` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `updated_time` DATETIME(6) DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_plugin_apprise_notify_log_channel_id` (`channel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Apprise 通知发送历史';
