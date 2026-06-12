-- 供应链管理系统 · 应用辅助表

CREATE TABLE IF NOT EXISTS scm_users (
    user_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户主键',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '登录用户名',
    password_hash CHAR(64) NOT NULL COMMENT 'SHA2 密码摘要',
    display_name VARCHAR(80) NOT NULL COMMENT '显示名称',
    department VARCHAR(30) NOT NULL COMMENT 'admin/procurement/sales/customer',
    role VARCHAR(30) NOT NULL COMMENT 'admin/manager/staff',
    can_view TINYINT(1) NOT NULL DEFAULT 1 COMMENT '查看权限',
    can_insert TINYINT(1) NOT NULL DEFAULT 0 COMMENT '新增权限',
    can_update TINYINT(1) NOT NULL DEFAULT 0 COMMENT '修改权限',
    can_delete TINYINT(1) NOT NULL DEFAULT 0 COMMENT '删除权限',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户与权限';

CREATE TABLE IF NOT EXISTS scm_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志主键',
    username VARCHAR(50) NOT NULL COMMENT '操作人',
    module VARCHAR(50) NOT NULL COMMENT '模块',
    action VARCHAR(30) NOT NULL COMMENT '动作',
    details TEXT NULL COMMENT '详情',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_scm_logs_created_at (created_at),
    INDEX idx_scm_logs_module (module),
    INDEX idx_scm_logs_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作审计日志';

CREATE TABLE IF NOT EXISTS scm_order_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '审计主键',
    order_key INT NOT NULL COMMENT '订单号',
    old_status VARCHAR(20) NULL COMMENT '原状态',
    new_status VARCHAR(20) NULL COMMENT '新状态',
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_scm_order_audit_order (order_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单状态变更审计';
