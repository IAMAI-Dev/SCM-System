-- 供应链管理系统 · 演示用户种子数据

INSERT INTO scm_users (
    username,
    password_hash,
    display_name,
    department,
    role,
    can_view,
    can_insert,
    can_update,
    can_delete
)
VALUES
(
    'admin',
    SHA2('123456', 256),
    '系统管理员',
    'admin',
    'manager',
    1,
    1,
    1,
    1
),
(
    'proc_mgr',
    SHA2('123456', 256),
    '采购经理',
    'procurement',
    'manager',
    1,
    1,
    1,
    0
),
(
    'proc_staff',
    SHA2('123456', 256),
    '采购专员',
    'procurement',
    'staff',
    1,
    1,
    0,
    0
),
(
    'sales_mgr',
    SHA2('123456', 256),
    '销售经理',
    'sales',
    'manager',
    1,
    1,
    1,
    0
)
ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    department = VALUES(department),
    role = VALUES(role),
    can_view = VALUES(can_view),
    can_insert = VALUES(can_insert),
    can_update = VALUES(can_update),
    can_delete = VALUES(can_delete),
    is_active = 1;
