"""用户认证与权限数据访问。"""

from __future__ import annotations

from core.db import cursor, transaction


def find_user_by_credentials(username: str, password: str) -> dict | None:
    """按用户名和密码摘要查询启用用户。"""
    sql = """
        SELECT
            user_id,
            username,
            display_name,
            department,
            role,
            can_view,
            can_insert,
            can_update,
            can_delete
        FROM scm_users
        WHERE username = %s
            AND password_hash = SHA2(%s, 256)
            AND is_active = 1
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql, (username, password))
        return db_cursor.fetchone()


def list_users() -> list[dict]:
    """查询系统用户列表。"""
    sql = """
        SELECT
            user_id,
            username,
            display_name,
            department,
            role,
            can_view,
            can_insert,
            can_update,
            can_delete,
            is_active,
            created_at
        FROM scm_users
        ORDER BY user_id ASC
    """
    with cursor() as db_cursor:
        db_cursor.execute(sql)
        return db_cursor.fetchall()


def update_permissions(
    user_id: int,
    can_view: bool,
    can_insert: bool,
    can_update: bool,
    can_delete: bool,
) -> None:
    """更新用户权限。"""
    sql = """
        UPDATE scm_users
        SET can_view = %s,
            can_insert = %s,
            can_update = %s,
            can_delete = %s
        WHERE user_id = %s
    """
    with transaction() as db_cursor:
        db_cursor.execute(
            sql,
            (
                int(can_view),
                int(can_insert),
                int(can_update),
                int(can_delete),
                user_id,
            ),
        )


def log_action(
    username: str,
    module: str,
    action: str,
    details: str,
) -> None:
    """写入操作审计日志。"""
    sql = """
        INSERT INTO scm_logs (username, module, action, details)
        VALUES (%s, %s, %s, %s)
    """
    with transaction() as db_cursor:
        db_cursor.execute(sql, (username, module, action, details))
