-- 供应链管理系统 · 存储过程

DROP PROCEDURE IF EXISTS sp_scm_dashboard_kpis;

DELIMITER $$
CREATE PROCEDURE sp_scm_dashboard_kpis()
BEGIN
    SELECT
        (SELECT COUNT(*) FROM Orders) AS total_orders,
        (SELECT COALESCE(SUM(Totalprice), 0) FROM Orders) AS total_revenue,
        (SELECT COUNT(*) FROM Customer) AS total_customers,
        (
            SELECT COUNT(*)
            FROM PartSupp
            WHERE Availqty < 100
        ) AS low_stock_count,
        (
            SELECT COUNT(*)
            FROM scm_logs
            WHERE created_at >= CURRENT_DATE
        ) AS today_log_count;
END$$
DELIMITER ;
