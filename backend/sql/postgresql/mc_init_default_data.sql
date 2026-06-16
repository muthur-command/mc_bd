-- PostgreSQL 初始化：建表 + 默认测试数据（与 backend/app/admin/model 一致）
-- 执行一次即可：若表不存在则创建，然后插入测试数据。测试账号密码均为 123456。

-- ========== 建表 ==========
-- 角色表
CREATE TABLE IF NOT EXISTS sys_role (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(32) NOT NULL,
    status INTEGER NOT NULL DEFAULT 1,
    remark TEXT NULL,
    created_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_time TIMESTAMPTZ NULL,
    CONSTRAINT sys_role_name_key UNIQUE (name)
);

COMMENT ON TABLE sys_role IS '角色表';

-- 用户表
CREATE TABLE IF NOT EXISTS sys_user (
    id BIGSERIAL PRIMARY KEY,
    uuid VARCHAR(64) NOT NULL,
    username VARCHAR(64) NOT NULL,
    nickname VARCHAR(64) NOT NULL,
    password VARCHAR(256) NULL,
    salt BYTEA NULL,
    email VARCHAR(256) NULL,
    phone VARCHAR(11) NULL,
    avatar VARCHAR(5000) NULL,
    status INTEGER NOT NULL DEFAULT 1,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_multi_login BOOLEAN NOT NULL DEFAULT FALSE,
    join_time TIMESTAMPTZ NOT NULL,
    last_login_time TIMESTAMPTZ NULL,
    last_password_changed_time TIMESTAMPTZ NULL,
    created_time TIMESTAMPTZ NOT NULL,
    updated_time TIMESTAMPTZ NULL,
    CONSTRAINT sys_user_uuid_key UNIQUE (uuid),
    CONSTRAINT sys_user_username_key UNIQUE (username),
    CONSTRAINT sys_user_email_key UNIQUE (email)
);

COMMENT ON TABLE sys_user IS '用户表';

CREATE INDEX IF NOT EXISTS ix_sys_user_username ON sys_user (username);
CREATE INDEX IF NOT EXISTS ix_sys_user_email ON sys_user (email);
CREATE INDEX IF NOT EXISTS ix_sys_user_status ON sys_user (status);

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS sys_user_role (
    id BIGSERIAL NOT NULL,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (id, user_id, role_id),
    CONSTRAINT uq_user_role UNIQUE (user_id, role_id)
);

COMMENT ON TABLE sys_user_role IS '用户角色关联表';

-- ========== 测试数据 ==========
INSERT INTO sys_role (id, name, status, remark, created_time, updated_time)
VALUES
(1, 'SuperAdmin', 1, NULL, now(), NULL),
(2, 'Development', 1, NULL, now(), NULL),
(3, 'Quality', 1, NULL, now(), NULL);

INSERT INTO sys_user (id, uuid, username, nickname, password, salt, email, phone, avatar, status, is_superuser, is_staff, is_multi_login, join_time, last_login_time, last_password_changed_time, created_time, updated_time)
VALUES
(1, gen_random_uuid()::text, 'superadmin', 'superadmin', '$2b$12$MPTegVRZ./e014xrNGWWPumqTD8QF2njT8xPPGltMoFETwq50iNGS', decode('243262243132244d5054656756525a2e2f6530313478724e4757575075', 'hex'), 'superadmin@mc.com', NULL, NULL, 1, TRUE, TRUE, TRUE, now(), now(), now(), now(), NULL),
(2, gen_random_uuid()::text, 'user', 'user', '$2b$12$MPTegVRZ./e014xrNGWWPumqTD8QF2njT8xPPGltMoFETwq50iNGS', decode('243262243132244d5054656756525a2e2f6530313478724e4757575075', 'hex'), 'user@mc.com', NULL, NULL, 1, FALSE, FALSE, FALSE, now(), now(), now(), now(), NULL);

INSERT INTO sys_user_role (id, user_id, role_id)
VALUES
(1, 1, 1),
(2, 2, 2);

SELECT setval(pg_get_serial_sequence('sys_role', 'id'), coalesce(max(id), 0) + 1, true) FROM sys_role;
SELECT setval(pg_get_serial_sequence('sys_user', 'id'), coalesce(max(id), 0) + 1, true) FROM sys_user;
SELECT setval(pg_get_serial_sequence('sys_user_role', 'id'), coalesce(max(id), 0) + 1, true) FROM sys_user_role;
