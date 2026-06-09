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
