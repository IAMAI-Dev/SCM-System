"""供应商数据访问。"""

from __future__ import annotations

from core.db import cursor


def list_suppliers(limit: int = 100) -> list[dict]:
    """查询供应商表现。"""
    sql = """
        SELECT
            supplier_key,
            supplier_name,
            nation_name,
            part_count,
            avg_supply_cost,
            total_available_qty
        FROM v_scm_supplier_performance
        ORDER BY part_count DESC, supplier_key ASC
        LIMIT %s
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql, (limit,))
        return db_cursor.fetchall()


def get_supplier_summary() -> dict:
    """查询供应商总体指标。"""
    sql = """
        SELECT
            COUNT(*) AS active_supplier_count,
            SUM(part_count) AS total_part_count,
            AVG(avg_supply_cost) AS avg_supply_cost,
            SUM(total_available_qty) AS total_available_qty
        FROM v_scm_supplier_performance
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql)
        return db_cursor.fetchone() or {}


def get_country_distribution(limit: int = 6) -> list[dict]:
    """查询供应商国家分布。"""
    sql = """
        SELECT
            nation_name,
            COUNT(*) AS supplier_count
        FROM v_scm_supplier_performance
        GROUP BY nation_name
        ORDER BY supplier_count DESC
        LIMIT %s
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql, (limit,))
        return db_cursor.fetchall()


def get_purchase_trend(limit: int = 6) -> list[dict]:
    """查询供应商相关采购额趋势。"""
    sql = """
        SELECT
            DATE_FORMAT(l.Receiptdate, '%%Y-%%m') AS month,
            SUM(l.Extendedprice) AS purchase_amount,
            COUNT(DISTINCT l.Suppkey) AS supplier_count
        FROM Lineitem l
        GROUP BY month
        ORDER BY month DESC
        LIMIT %s
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql, (limit,))
        return list(reversed(db_cursor.fetchall()))
