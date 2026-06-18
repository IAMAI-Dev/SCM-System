"""供应商数据访问。"""

from __future__ import annotations

from core.db import cursor


def list_suppliers(limit: int = 100) -> list[dict]:
    """查询供应商表现。"""
    sql = """
        SELECT
            s.Suppkey AS supplier_key,
            s.Name AS supplier_name,
            n.Name AS nation_name,
            COUNT(ps.Partkey) AS part_count,
            AVG(ps.Supplycost) AS avg_supply_cost,
            SUM(ps.Availqty) AS total_available_qty
        FROM Supplier s
        JOIN Nation n ON n.Nationkey = s.Nationkey
        LEFT JOIN PartSupp ps ON ps.Suppkey = s.Suppkey
        GROUP BY s.Suppkey, s.Name, n.Name
        ORDER BY part_count DESC, supplier_key ASC
        LIMIT %s
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql, (_safe_limit(limit, 200),))
        return db_cursor.fetchall()


def get_supplier_summary() -> dict:
    """查询供应商总体指标。"""
    sql = """
        SELECT
            (SELECT COUNT(*) FROM Supplier) AS active_supplier_count,
            (SELECT COUNT(*) FROM PartSupp) AS total_part_count,
            (SELECT AVG(Supplycost) FROM PartSupp) AS avg_supply_cost,
            (SELECT SUM(Availqty) FROM PartSupp) AS total_available_qty
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql)
        return db_cursor.fetchone() or {}


def get_country_distribution(limit: int = 6) -> list[dict]:
    """查询供应商国家分布。"""
    sql = """
        SELECT
            n.Name AS nation_name,
            COUNT(*) AS supplier_count
        FROM Supplier s
        JOIN Nation n ON n.Nationkey = s.Nationkey
        GROUP BY n.Name
        ORDER BY supplier_count DESC
        LIMIT %s
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql, (_safe_limit(limit, 20),))
        return db_cursor.fetchall()


def get_purchase_trend(
    limit: int = 6,
    row_limit: int = 20000,
) -> list[dict]:
    """查询供应商相关采购额趋势。"""
    sql = """
        SELECT
            DATE_FORMAT(recent.Receiptdate, '%Y-%m') AS month,
            SUM(recent.Extendedprice) AS purchase_amount,
            COUNT(DISTINCT recent.Suppkey) AS supplier_count
        FROM (
            SELECT Receiptdate, Extendedprice, Suppkey
            FROM Lineitem
            ORDER BY Receiptdate DESC
            LIMIT %s
        ) recent
        GROUP BY month
        ORDER BY month DESC
        LIMIT %s
    """
    with cursor() as db_cursor:
        db_cursor.execute(
            sql,
            (
                _safe_limit(row_limit, 50000),
                _safe_limit(limit, 24),
            ),
        )
        return list(reversed(db_cursor.fetchall()))


def _safe_limit(value: int, maximum: int) -> int:
    """限制查询条数，避免误传过大的首屏查询。"""
    return max(1, min(int(value), maximum))
