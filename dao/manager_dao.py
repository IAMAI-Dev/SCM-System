"""经营分析数据访问。"""

from __future__ import annotations

from core.db import cursor


def get_monthly_revenue() -> list[dict]:
    """按月份统计有效发货明细营收。"""
    sql = """
        SELECT
            DATE_FORMAT(Shipdate, '%Y-%m') AS month,
            SUM(Extendedprice * (1 - Discount)) AS revenue
        FROM Lineitem
        WHERE Shipdate IS NOT NULL
        GROUP BY month
        HAVING revenue IS NOT NULL
        ORDER BY month
        LIMIT 12
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql)
        return db_cursor.fetchall()


def get_top_parts() -> list[dict]:
    """统计销量最高的零件。"""
    sql = """
        SELECT
            p.Name AS part_name,
            SUM(l.Quantity) AS total_qty
        FROM Lineitem l
        JOIN Part p ON l.Partkey = p.Partkey
        GROUP BY p.Partkey, p.Name
        ORDER BY total_qty DESC
        LIMIT 10
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql)
        return db_cursor.fetchall()


def get_customer_value() -> list[dict]:
    """统计客户余额与订单数量分布。"""
    sql = """
        SELECT
            c.Name AS customer_name,
            c.Acctbal AS balance,
            COUNT(o.Orderkey) AS order_count
        FROM (
            SELECT Custkey, Name, Acctbal
            FROM Customer
            ORDER BY Custkey
            LIMIT 30
        ) c
        LEFT JOIN Orders o ON c.Custkey = o.Custkey
        GROUP BY c.Custkey, c.Name, c.Acctbal
        ORDER BY c.Custkey
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql)
        return db_cursor.fetchall()
