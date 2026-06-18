"""数据库性能统计数据访问。"""

from core.db import cursor


def get_table_stats():
    """获取所有表的大小（MB）和行数。"""
    with cursor() as db_cursor:
        sql = """
            SELECT
                table_name AS name,
                ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb,
                table_rows AS row_count
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            ORDER BY size_mb DESC;
        """
        db_cursor.execute(sql)
        return db_cursor.fetchall()


def get_unused_indexes():
    """获取非主键索引清单（仅供性能调优参考）。"""
    with cursor() as db_cursor:
        sql = """
            SELECT
                t.table_name,
                i.index_name,
                CASE WHEN i.non_unique = 0 THEN '是' ELSE '否' END AS is_unique
            FROM information_schema.tables t
            JOIN information_schema.statistics i
                ON t.table_schema = i.table_schema
                AND t.table_name = i.table_name
            WHERE t.table_schema = DATABASE()
            AND i.index_name != 'PRIMARY'
            LIMIT 10;
        """
        db_cursor.execute(sql)
        return db_cursor.fetchall()
