-- 供应链管理系统 · 演示用户种子数据

UPDATE scm_users
SET is_active = 0
WHERE username NOT IN (
    'admin',
    'David',
    'Tom',
    'Jerry',
    'Marry',
    'Jack',
    'Mike'
);

INSERT INTO scm_users (
    username,
    password_hash,
    display_name,
    department,
    role,
    can_view,
    can_insert,
    can_update,
    can_delete,
    is_active
)
VALUES
(
    'admin',
    SHA2('123456', 256),
    '系统管理员',
    'admin',
    'admin',
    1,
    1,
    1,
    1,
    1
),
(
    'David',
    SHA2('123456', 256),
    'David',
    'procurement',
    'manager',
    1,
    1,
    1,
    1,
    1
),
(
    'Tom',
    SHA2('123456', 256),
    'Tom',
    'sales',
    'manager',
    1,
    1,
    1,
    1,
    1
),
(
    'Jerry',
    SHA2('123456', 256),
    'Jerry',
    'customer',
    'manager',
    1,
    1,
    1,
    1,
    1
),
(
    'Marry',
    SHA2('123456', 256),
    'Marry',
    'procurement',
    'staff',
    1,
    1,
    0,
    0,
    1
),
(
    'Jack',
    SHA2('123456', 256),
    'Jack',
    'sales',
    'staff',
    1,
    1,
    0,
    0,
    1
),
(
    'Mike',
    SHA2('123456', 256),
    'Mike',
    'customer',
    'staff',
    1,
    1,
    0,
    0,
    1
)
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    display_name = VALUES(display_name),
    department = VALUES(department),
    role = VALUES(role),
    can_view = VALUES(can_view),
    can_insert = VALUES(can_insert),
    can_update = VALUES(can_update),
    can_delete = VALUES(can_delete),
    is_active = 1;

-- 为课程基础数据补充演示字段，避免经营分析图表因 NULL 日期/余额显示为空。
UPDATE Customer
SET Acctbal = ROUND(500 + MOD(Custkey * 137, 20000), 2)
WHERE Acctbal IS NULL;

UPDATE Lineitem
SET
    Shipdate = DATE_SUB(CURRENT_DATE, INTERVAL MOD(Orderkey + Linenumber, 365) DAY),
    Commitdate = COALESCE(
        Commitdate,
        DATE_SUB(CURRENT_DATE, INTERVAL MOD(Orderkey + Linenumber + 3, 365) DAY)
    ),
    Receiptdate = DATE_ADD(
        DATE_SUB(CURRENT_DATE, INTERVAL MOD(Orderkey + Linenumber, 365) DAY),
        INTERVAL 2 DAY
    )
WHERE Shipdate IS NULL OR Receiptdate IS NULL;
