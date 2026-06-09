"""客户数据访问。"""

from __future__ import annotations

from core.db import cursor, transaction


def list_customers(search_key: str = "", limit: int = 100) -> list[dict]:
    """查询客户摘要。"""
    sql = """
        SELECT
            customer_key,
            customer_name,
            nation_name,
            phone,
            account_balance,
            order_count,
            total_revenue
        FROM v_scm_customer_summary
    """
    params: tuple = (limit,)
    if search_key:
        sql += " WHERE customer_key = %s OR customer_name LIKE %s"
        params = (search_key, f"%{search_key}%", limit)
    sql += " ORDER BY customer_key ASC LIMIT %s"
    with cursor() as db_cursor:
        db_cursor.execute(sql, params)
        return db_cursor.fetchall()


def create_customer(data: dict) -> int:
    """新增客户。"""
    with transaction() as db_cursor:
        db_cursor.execute("SELECT COALESCE(MAX(Custkey), 0) + 1 AS next_id "
                          "FROM Customer")
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


def update_customer(cust_key: int, data: dict) -> None:
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
    with transaction() as db_cursor:
        db_cursor.execute(
            sql,
            (
                data["name"],
                data["address"],
                data["phone"],
                data["account_balance"],
                data["market_segment"],
                cust_key,
            ),
        )


def delete_customer(cust_key: int) -> None:
    """删除客户。"""
    with transaction() as db_cursor:
        db_cursor.execute("DELETE FROM Customer WHERE Custkey = %s",
                          (cust_key,))
