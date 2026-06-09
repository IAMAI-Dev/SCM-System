"""审计日志数据访问。"""

from __future__ import annotations

from core.db import cursor


def list_logs(limit: int = 200) -> list[dict]:
    """查询最近审计日志。"""
    sql = """
        SELECT
            log_id,
            username,
            module,
            action,
            details,
            created_at
        FROM scm_logs
        ORDER BY created_at DESC, log_id DESC
        LIMIT %s
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql, (limit,))
        return db_cursor.fetchall()
