-- 分析页面查询索引。动态语句允许兼容已经手工创建过索引的数据库。

SET @index_exists = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
        AND table_name = 'Orders'
        AND index_name = 'idx_orders_custkey'
);
SET @index_sql = IF(
    @index_exists = 0,
    'CREATE INDEX idx_orders_custkey ON Orders (Custkey)',
    'SELECT 1'
);
PREPARE index_statement FROM @index_sql;
EXECUTE index_statement;
DEALLOCATE PREPARE index_statement;

SET @index_exists = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
        AND table_name = 'Lineitem'
        AND index_name = 'idx_lineitem_shipdate'
);
SET @index_sql = IF(
    @index_exists = 0,
    'CREATE INDEX idx_lineitem_shipdate ON Lineitem (Shipdate)',
    'SELECT 1'
);
PREPARE index_statement FROM @index_sql;
EXECUTE index_statement;
DEALLOCATE PREPARE index_statement;

SET @index_exists = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
        AND table_name = 'Lineitem'
        AND index_name = 'idx_lineitem_receiptdate'
);
SET @index_sql = IF(
    @index_exists = 0,
    'CREATE INDEX idx_lineitem_receiptdate ON Lineitem (Receiptdate)',
    'SELECT 1'
);
PREPARE index_statement FROM @index_sql;
EXECUTE index_statement;
DEALLOCATE PREPARE index_statement;

SET @index_exists = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
        AND table_name = 'Lineitem'
        AND index_name = 'idx_lineitem_partkey'
);
SET @index_sql = IF(
    @index_exists = 0,
    'CREATE INDEX idx_lineitem_partkey ON Lineitem (Partkey)',
    'SELECT 1'
);
PREPARE index_statement FROM @index_sql;
EXECUTE index_statement;
DEALLOCATE PREPARE index_statement;

SET @index_exists = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
        AND table_name = 'Lineitem'
        AND index_name = 'idx_lineitem_suppkey'
);
SET @index_sql = IF(
    @index_exists = 0,
    'CREATE INDEX idx_lineitem_suppkey ON Lineitem (Suppkey)',
    'SELECT 1'
);
PREPARE index_statement FROM @index_sql;
EXECUTE index_statement;
DEALLOCATE PREPARE index_statement;

SET @index_exists = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
        AND table_name = 'PartSupp'
        AND index_name = 'idx_partsupp_suppkey'
);
SET @index_sql = IF(
    @index_exists = 0,
    'CREATE INDEX idx_partsupp_suppkey ON PartSupp (Suppkey)',
    'SELECT 1'
);
PREPARE index_statement FROM @index_sql;
EXECUTE index_statement;
DEALLOCATE PREPARE index_statement;
