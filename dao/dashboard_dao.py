"""仪表盘数据访问。"""

from __future__ import annotations

from core.db import cursor, get_connection


def get_dashboard_kpis() -> dict:
    """调用存储过程读取仪表盘 KPI。"""
    conn = get_connection()
    db_cursor = conn.cursor(dictionary=True)
    try:
        db_cursor.callproc("sp_scm_dashboard_kpis")
        for result in db_cursor.stored_results():
            row = result.fetchone()
            if row:
                return row
        return {}
    finally:
        db_cursor.close()
        conn.close()


def get_dashboard_kpis_fallback() -> dict:
    """存储过程不可用时使用普通 SQL 查询 KPI。"""
    queries = {
        "total_orders": "SELECT COUNT(*) AS value FROM Orders",
        "total_revenue": (
            "SELECT COALESCE(SUM(Totalprice), 0) AS value FROM Orders"
        ),
        "total_customers": "SELECT COUNT(*) AS value FROM Customer",
        "low_stock_count": (
            "SELECT COUNT(*) AS value FROM PartSupp WHERE Availqty < 100"
        ),
    }
    result = {}
    with cursor() as db_cursor:
        for key, sql in queries.items():
            db_cursor.execute(sql)
            row = db_cursor.fetchone()
            result[key] = row["value"] if row else 0
    result["today_log_count"] = 0
    return result


def get_sales_history(limit: int = 8) -> list[dict]:
    """读取近期销售趋势（限定日期范围利用索引）。"""
    sql = """
        SELECT
            DATE_FORMAT(order_date, '%Y-%m') AS month,
            SUM(total_revenue) AS revenue,
            SUM(order_count) AS order_count
        FROM v_scm_daily_sales
        WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
        GROUP BY month
        ORDER BY month DESC
        LIMIT %s
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql, (limit, limit))
        return list(reversed(db_cursor.fetchall()))


def get_low_stock_snapshot(limit: int = 8) -> list[dict]:
    """读取低库存快照。"""
    sql = """
        SELECT
            part_key,
            part_name,
            supplier_name,
            avail_qty,
            supply_cost,
            stock_status
        FROM v_scm_inventory_status
        WHERE stock_status IN ('low', 'warning')
        ORDER BY avail_qty ASC
        LIMIT %s
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql, (limit,))
        return db_cursor.fetchall()
