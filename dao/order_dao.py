"""订单数据访问。"""

from __future__ import annotations

from core.db import cursor, transaction


def list_orders(search_key: str = "", limit: int = 100) -> list[dict]:
    """查询订单列表。"""
    base_sql = """
        SELECT
            o.Orderkey AS order_key,
            c.Name AS customer_name,
            o.Totalprice AS total_price,
            o.Orderstatus AS order_status,
            o.Orderdate AS order_date,
            o.Orderpriority AS order_priority
        FROM Orders o
        JOIN Customer c ON c.Custkey = o.Custkey
    """
    params: list = []
    if search_key:
        conditions = ["c.Name LIKE %s"]
        params.append(f"%{search_key}%")
        if search_key.isdigit():
            conditions.insert(0, "o.Orderkey = %s")
            params.insert(0, int(search_key))
        base_sql += " WHERE " + " OR ".join(conditions)
    sql = base_sql + " ORDER BY o.Orderkey DESC LIMIT %s"
    params.append(limit)
    with cursor() as db_cursor:
        db_cursor.execute(sql, tuple(params))
        return db_cursor.fetchall()


def list_order_details(order_key: int) -> list[dict]:
    """查询订单明细。"""
    sql = """
        SELECT
            l.Linenumber AS line_number,
            l.Partkey AS part_key,
            p.Name AS part_name,
            l.Suppkey AS supplier_key,
            s.Name AS supplier_name,
            l.Quantity AS quantity,
            l.Extendedprice AS extended_price,
            l.Discount AS discount,
            l.Linestatus AS line_status
        FROM Lineitem l
        JOIN Part p ON p.Partkey = l.Partkey
        JOIN Supplier s ON s.Suppkey = l.Suppkey
        WHERE l.Orderkey = %s
        ORDER BY l.Linenumber ASC
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql, (order_key,))
        return db_cursor.fetchall()


def update_order_status(
    order_key: int,
    status: str,
    db_cursor=None,
) -> bool:
    """更新订单状态。"""
    sql = """
        UPDATE Orders
        SET Orderstatus = %s
        WHERE Orderkey = %s
    """
    if db_cursor is not None:
        return _update_order_status(db_cursor, sql, order_key, status)

    with transaction() as tx_cursor:
        return _update_order_status(tx_cursor, sql, order_key, status)


def _update_order_status(
    db_cursor,
    sql: str,
    order_key: int,
    status: str,
) -> bool:
    """锁定订单并更新状态，返回是否实际变更。"""
    db_cursor.execute(
        "SELECT Orderstatus FROM Orders WHERE Orderkey = %s FOR UPDATE",
        (order_key,),
    )
    row = db_cursor.fetchone()
    if row is None:
        raise ValueError("订单不存在。")
    if row["Orderstatus"] == status:
        return False
    db_cursor.execute(sql, (status, order_key))
    return True


def create_order(
    cust_key: int,
    items: list[dict],
    db_cursor=None,
) -> int:
    """使用事务创建订单并扣减库存。"""
    if db_cursor is not None:
        return _create_order(db_cursor, cust_key, items)

    with transaction() as tx_cursor:
        return _create_order(tx_cursor, cust_key, items)


def _create_order(db_cursor, cust_key: int, items: list[dict]) -> int:
    """执行订单创建 SQL。"""
    if not items:
        raise ValueError("订单明细不能为空。")

    db_cursor.execute(
        "SELECT COALESCE(MAX(Orderkey), 0) + 1 AS next_id FROM Orders"
    )
    new_order_key = db_cursor.fetchone()["next_id"]
    total_price = 0.0
    line_rows = []

    for index, item in enumerate(items, start=1):
        part_key = int(item["part_key"])
        supplier_key = int(item["supplier_key"])
        quantity = int(item["quantity"])

        db_cursor.execute(
            """
            SELECT Availqty, Supplycost
            FROM PartSupp
            WHERE Partkey = %s AND Suppkey = %s
            FOR UPDATE
            """,
            (part_key, supplier_key),
        )
        stock_row = db_cursor.fetchone()
        if not stock_row:
            raise ValueError("零件与供应商关系不存在。")
        if int(stock_row["Availqty"]) < quantity:
            raise ValueError("库存不足，订单已回滚。")

        price = float(stock_row["Supplycost"]) * quantity * 1.5
        total_price += price
        line_rows.append(
            (
                new_order_key,
                part_key,
                supplier_key,
                index,
                quantity,
                price,
                0.05,
                0.04,
                "N",
                "O",
            )
        )

        db_cursor.execute(
            """
            UPDATE PartSupp
            SET Availqty = Availqty - %s
            WHERE Partkey = %s AND Suppkey = %s
            """,
            (quantity, part_key, supplier_key),
        )

    db_cursor.execute(
        """
        INSERT INTO Orders (
            Orderkey,
            Custkey,
            Orderstatus,
            Totalprice,
            Orderdate,
            Orderpriority,
            Clerk,
            Shippriority,
            Comment
        )
        VALUES (
            %s,
            %s,
            'O',
            %s,
            CURRENT_DATE,
            '1-URGENT',
            'Clerk#SCM',
            0,
            'Created by SCM desktop'
        )
        """,
        (new_order_key, cust_key, total_price),
    )
    db_cursor.executemany(
        """
        INSERT INTO Lineitem (
            Orderkey,
            Partkey,
            Suppkey,
            Linenumber,
            Quantity,
            Extendedprice,
            Discount,
            Tax,
            Returnflag,
            Linestatus,
            Shipdate,
            Commitdate,
            Receiptdate,
            Shipinstruct,
            Shipmode,
            Comment
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            CURRENT_DATE,
            CURRENT_DATE,
            CURRENT_DATE,
            'DELIVER IN PERSON',
            'TRUCK',
            'Created by SCM desktop'
        )
        """,
        line_rows,
    )
    return new_order_key
