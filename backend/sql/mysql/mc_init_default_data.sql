-- MySQL 初始化：建表 + 测试数据（与 backend/app/admin/model 一致）
-- 执行一次即可：若表不存在则创建，然后插入测试数据。测试账号密码均为 123456。

-- ========== 建表 ==========
-- 角色表
CREATE TABLE IF NOT EXISTS sys_role (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
    name VARCHAR(32) NOT NULL COMMENT '角色名称',
    status INT NOT NULL DEFAULT 1 COMMENT '角色状态（0停用 1正常）',
    remark LONGTEXT NULL COMMENT '备注',
    created_time DATETIME NOT NULL COMMENT '创建时间',
    updated_time DATETIME NULL COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY (name)
) COMMENT '角色表';

-- 用户表
CREATE TABLE IF NOT EXISTS sys_user (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
    uuid VARCHAR(64) NOT NULL COMMENT '用户 UUID',
    username VARCHAR(64) NOT NULL COMMENT '用户名',
    nickname VARCHAR(64) NOT NULL COMMENT '昵称',
    password VARCHAR(256) NULL COMMENT '密码',
    salt VARBINARY(255) NULL COMMENT '加密盐',
    email VARCHAR(256) NULL COMMENT '邮箱',
    phone VARCHAR(11) NULL COMMENT '手机号',
    avatar VARCHAR(5000) NULL COMMENT '头像 URL 或 data URI',
    status INT NOT NULL DEFAULT 1 COMMENT '用户账号状态(0停用 1正常)',
    is_superuser TINYINT(1) NOT NULL DEFAULT 0 COMMENT '超级权限(0否 1是)',
    is_staff TINYINT(1) NOT NULL DEFAULT 0 COMMENT '后台管理登陆(0否 1是)',
    is_multi_login TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否重复登陆(0否 1是)',
    join_time DATETIME NOT NULL COMMENT '注册时间',
    last_login_time DATETIME NULL COMMENT '上次登录时间',
    last_password_changed_time DATETIME NULL COMMENT '上次密码变更时间',
    created_time DATETIME NOT NULL COMMENT '创建时间',
    updated_time DATETIME NULL COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY (uuid),
    UNIQUE KEY (username),
    KEY (email),
    KEY (status)
) COMMENT '用户表';

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS sys_user_role (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role_id BIGINT NOT NULL COMMENT '角色ID',
    PRIMARY KEY (id, user_id, role_id),
    UNIQUE KEY uq_user_role (user_id, role_id)
) COMMENT '用户角色关联表';

-- ========== 测试数据 ==========
INSERT INTO sys_role (id, name, status, remark, created_time, updated_time)
VALUES
(1, 'SuperAdmin', 1, NULL, NOW(), NULL),
(2, 'Development', 1, NULL, NOW(), NULL),
(3, 'Quality', 1, NULL, NOW(), NULL);

INSERT INTO sys_user (id, uuid, username, nickname, password, salt, email, phone, avatar, status, is_superuser, is_staff, is_multi_login, join_time, last_login_time, last_password_changed_time, created_time, updated_time)
VALUES
(1, UUID(), 'superadmin', 'superadmin', '$2b$12$MPTegVRZ./e014xrNGWWPumqTD8QF2njT8xPPGltMoFETwq50iNGS', UNHEX('243262243132244d5054656756525a2e2f6530313478724e4757575075'), 'superadmin@mc.com', NULL, NULL, 1, TRUE, TRUE, TRUE, NOW(), NOW(), NOW(), NOW(), NULL),
(2, UUID(), 'user', 'user', '$2b$12$MPTegVRZ./e014xrNGWWPumqTD8QF2njT8xPPGltMoFETwq50iNGS', UNHEX('243262243132244d5054656756525a2e2f6530313478724e4757575075'), 'user@mc.com', NULL, NULL, 1, FALSE, FALSE, FALSE, NOW(), NOW(), NOW(), NOW(), NULL);

INSERT INTO sys_user_role (id, user_id, role_id)
VALUES
(1, 1, 1),
(2, 2, 2);
