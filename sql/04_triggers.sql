-- 供应链管理系统 · 触发器

DROP TRIGGER IF EXISTS trg_scm_users_after_insert;
DROP TRIGGER IF EXISTS trg_scm_users_after_update;
DROP TRIGGER IF EXISTS trg_scm_orders_status_update;

DELIMITER $$
CREATE TRIGGER trg_scm_users_after_insert
AFTER INSERT ON scm_users
FOR EACH ROW
BEGIN
    INSERT INTO scm_logs (username, module, action, details)
    VALUES (
        'system',
        'users',
        'INSERT',
        CONCAT('创建用户: ', NEW.username)
    );
END$$

CREATE TRIGGER trg_scm_users_after_update
AFTER UPDATE ON scm_users
FOR EACH ROW
BEGIN
    INSERT INTO scm_logs (username, module, action, details)
    VALUES (
        'system',
        'users',
        'UPDATE',
        CONCAT('更新用户: ', NEW.username)
    );
END$$

CREATE TRIGGER trg_scm_orders_status_update
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
    IF OLD.Orderstatus <> NEW.Orderstatus THEN
        INSERT INTO scm_order_audit (
            order_key,
            old_status,
            new_status
        )
        VALUES (
            NEW.Orderkey,
            OLD.Orderstatus,
            NEW.Orderstatus
        );
    END IF;
END$$
DELIMITER ;
