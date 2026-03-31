-- Bento 布局插件表（MySQL）
-- 与 backend.plugin.bento_layout.model.bento_layout.BentoLayoutRecord 一致

CREATE TABLE IF NOT EXISTS `plugin_bento_layout` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `page_id` VARCHAR(255) NOT NULL COMMENT '页面 ID',
  `layout_data` LONGTEXT NOT NULL COMMENT '布局 JSON',
  `created_time` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `updated_time` DATETIME(6) DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_plugin_bento_layout_page_id` (`page_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bento 布局表';
