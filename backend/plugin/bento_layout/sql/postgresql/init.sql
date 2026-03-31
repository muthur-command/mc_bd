-- Bento 布局插件表（PostgreSQL）

CREATE TABLE IF NOT EXISTS plugin_bento_layout (
  id BIGSERIAL PRIMARY KEY,
  page_id VARCHAR(255) NOT NULL,
  layout_data TEXT NOT NULL,
  created_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_time TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_plugin_bento_layout_page_id ON plugin_bento_layout (page_id);

COMMENT ON TABLE plugin_bento_layout IS 'Bento 布局表';
