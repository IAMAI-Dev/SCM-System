-- 供应链管理系统 · 数据库视图

CREATE OR REPLACE VIEW v_scm_inventory_status AS
SELECT
    ps.Partkey AS part_key,
    p.Name AS part_name,
    p.Brand AS part_brand,
    ps.Suppkey AS supplier_key,
    s.Name AS supplier_name,
    ps.Availqty AS avail_qty,
    ps.Supplycost AS supply_cost,
    CASE
        WHEN ps.Availqty < 100 THEN 'low'
        WHEN ps.Availqty < 500 THEN 'warning'
        ELSE 'normal'
    END AS stock_status
FROM PartSupp ps
JOIN Part p ON p.Partkey = ps.Partkey
JOIN Supplier s ON s.Suppkey = ps.Suppkey;

CREATE OR REPLACE VIEW v_scm_daily_sales AS
SELECT
    o.Orderdate AS order_date,
    COUNT(*) AS order_count,
    SUM(o.Totalprice) AS total_revenue
FROM Orders o
GROUP BY o.Orderdate;

CREATE OR REPLACE VIEW v_scm_supplier_performance AS
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
GROUP BY s.Suppkey, s.Name, n.Name;

CREATE OR REPLACE VIEW v_scm_customer_summary AS
SELECT
    c.Custkey AS customer_key,
    c.Name AS customer_name,
    n.Name AS nation_name,
    c.Phone AS phone,
    c.Acctbal AS account_balance,
    COUNT(o.Orderkey) AS order_count,
    COALESCE(SUM(o.Totalprice), 0) AS total_revenue
FROM Customer c
JOIN Nation n ON n.Nationkey = c.Nationkey
LEFT JOIN Orders o ON o.Custkey = c.Custkey
GROUP BY c.Custkey, c.Name, n.Name, c.Phone, c.Acctbal;
