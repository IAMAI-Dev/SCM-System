"""库存数据访问。"""

from __future__ import annotations

from core.db import cursor, transaction


def list_inventory(low_only: bool = False, limit: int = 200) -> list[dict]:
    """查询库存列表。"""
    sql = """
        SELECT
            part_key,
            part_name,
            part_brand,
            supplier_key,
            supplier_name,
            avail_qty,
            supply_cost,
            stock_status
        FROM v_scm_inventory_status
    """
    params: tuple = (limit,)
    if low_only:
        sql += " WHERE stock_status IN ('low', 'warning')"
    sql += " ORDER BY avail_qty ASC LIMIT %s"
    with cursor() as db_cursor:
        db_cursor.execute(sql, params)
        return db_cursor.fetchall()


def replenish(
    part_key: int,
    supplier_key: int,
    quantity: int,
    db_cursor=None,
) -> None:
    """补充库存数量。"""
    sql = """
        UPDATE PartSupp
        SET Availqty = Availqty + %s
        WHERE Partkey = %s AND Suppkey = %s
    """
    params = (quantity, part_key, supplier_key)
    if db_cursor is not None:
        _execute_replenish(db_cursor, sql, params)
        return

    with transaction() as tx_cursor:
        _execute_replenish(tx_cursor, sql, params)


def _execute_replenish(db_cursor, sql: str, params: tuple) -> None:
    """执行补货并检查库存关系。"""
    db_cursor.execute(sql, params)
    if db_cursor.rowcount == 0:
        raise ValueError("零件与供应商库存关系不存在。")


def list_stock_values() -> list[dict]:
    """查询库存价值，用于 ABC 分类。"""
    sql = """
        SELECT
            Partkey AS part_key,
            Suppkey AS supplier_key,
            Availqty AS avail_qty,
            Supplycost AS supply_cost,
            Availqty * Supplycost AS stock_value
        FROM PartSupp
        ORDER BY stock_value DESC
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql)
        return db_cursor.fetchall()
