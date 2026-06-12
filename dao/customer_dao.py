"""客户数据访问。"""

from __future__ import annotations

from core.db import cursor, transaction


def list_customers(search_key: str = "", limit: int = 100) -> list[dict]:
    """查询客户摘要。"""
    safe_limit = max(1, min(int(limit), 500))
    sql = """
        SELECT
            c.Custkey AS customer_key,
            c.Name AS customer_name,
            n.Name AS nation_name,
            c.Phone AS phone,
            c.Acctbal AS account_balance,
            COUNT(o.Orderkey) AS order_count,
            COALESCE(SUM(o.Totalprice), 0) AS total_revenue
        FROM (
            SELECT
                cbase.Custkey,
                cbase.Name,
                cbase.Nationkey,
                cbase.Phone,
                cbase.Acctbal
            FROM Customer cbase
    """
    params: list = []
    if search_key:
        if search_key.isdigit():
            sql += " WHERE cbase.Custkey = %s OR cbase.Name LIKE %s"
            params.extend([int(search_key), f"%{search_key}%"])
        else:
            sql += " WHERE cbase.Name LIKE %s"
            params.append(f"%{search_key}%")
    sql += """
            ORDER BY cbase.Custkey ASC
            LIMIT %s
        ) c
        JOIN Nation n ON n.Nationkey = c.Nationkey
        LEFT JOIN Orders o ON o.Custkey = c.Custkey
        GROUP BY c.Custkey, c.Name, n.Name, c.Phone, c.Acctbal
        ORDER BY c.Custkey ASC
    """
    params.append(safe_limit)
    with cursor() as db_cursor:
        db_cursor.execute(sql, tuple(params))
        return db_cursor.fetchall()


def create_customer(data: dict, db_cursor=None) -> int:
    """新增客户。"""
    if db_cursor is not None:
        return _create_customer(db_cursor, data)

    with transaction() as tx_cursor:
        return _create_customer(tx_cursor, data)


def _create_customer(db_cursor, data: dict) -> int:
    """执行客户新增 SQL。"""
    db_cursor.execute(
        "SELECT COALESCE(MAX(Custkey), 0) + 1 AS next_id FROM Customer"
    )
    cust_key = db_cursor.fetchone()["next_id"]
    db_cursor.execute(
        """
        INSERT INTO Customer (
            Custkey,
            Name,
            Address,
            Nationkey,
            Phone,
            Acctbal,
            Mktsegment,
            Comment
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            cust_key,
            data["name"],
            data["address"],
            data["nation_key"],
            data["phone"],
            data["account_balance"],
            data["market_segment"],
            data["comment"],
        ),
    )
    return cust_key


def update_customer(cust_key: int, data: dict, db_cursor=None) -> None:
    """更新客户基础资料。"""
    sql = """
        UPDATE Customer
        SET Name = %s,
            Address = %s,
            Phone = %s,
            Acctbal = %s,
            Mktsegment = %s
        WHERE Custkey = %s
    """
    params = (
        data["name"],
        data["address"],
        data["phone"],
        data["account_balance"],
        data["market_segment"],
        cust_key,
    )
    if db_cursor is not None:
        _update_existing_customer(db_cursor, sql, params, cust_key)
        return

    with transaction() as tx_cursor:
        _update_existing_customer(tx_cursor, sql, params, cust_key)


def delete_customer(cust_key: int, db_cursor=None) -> None:
    """删除客户。"""
    sql = "DELETE FROM Customer WHERE Custkey = %s"
    params = (cust_key,)
    if db_cursor is not None:
        _execute_customer_change(db_cursor, sql, params, "客户不存在。")
        return

    with transaction() as tx_cursor:
        _execute_customer_change(tx_cursor, sql, params, "客户不存在。")


def _execute_customer_change(
    db_cursor,
    sql: str,
    params: tuple,
    missing_message: str,
) -> None:
    """执行客户变更并检查目标行。"""
    db_cursor.execute(sql, params)
    if db_cursor.rowcount == 0:
        raise ValueError(missing_message)


def _update_existing_customer(
    db_cursor,
    sql: str,
    params: tuple,
    cust_key: int,
) -> None:
    """确认客户存在后执行更新，允许无变化保存。"""
    db_cursor.execute(
        "SELECT Custkey FROM Customer WHERE Custkey = %s FOR UPDATE",
        (cust_key,),
    )
    if db_cursor.fetchone() is None:
        raise ValueError("客户不存在。")
    db_cursor.execute(sql, params)
