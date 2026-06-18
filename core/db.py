"""数据库连接池与事务辅助模块。"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import mysql.connector
from mysql.connector import pooling

from core.config import PROJECT_ROOT, load_database_config


_pool: pooling.MySQLConnectionPool | None = None

MIGRATION_SCRIPTS = (
    "01_app_tables.sql",
    "02_views.sql",
    "03_procedures.sql",
    "04_triggers.sql",
    "05_seed.sql",
    "06.sql",
    "07_performance_indexes.sql",
)
BASELINE_SCRIPTS = MIGRATION_SCRIPTS[:-1]


class DatabaseError(RuntimeError):
    """应用层数据库异常。"""


def get_pool() -> pooling.MySQLConnectionPool:
    """获取全局 MySQL 连接池。"""
    global _pool
    if _pool is None:
        config = load_database_config()
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name=config.pool_name,
                pool_size=config.pool_size,
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.database,
                charset="utf8mb4",
                use_unicode=True,
                use_pure=True,
            )
        except mysql.connector.Error as exc:
            raise DatabaseError(
                "无法连接到 MySQL 数据库，请检查 config.ini 或环境变量。"
                f"\n原始错误：{exc}"
            ) from exc
    return _pool


def get_connection():
    """从连接池获取数据库连接。"""
    try:
        return get_pool().get_connection()
    except mysql.connector.Error as exc:
        raise DatabaseError(f"获取数据库连接失败：{exc}") from exc


@contextmanager
def cursor(dictionary: bool = True) -> Iterator:
    """提供自动释放的游标上下文。"""
    conn = get_connection()
    db_cursor = conn.cursor(dictionary=dictionary)
    try:
        yield db_cursor
    except mysql.connector.Error as exc:
        raise DatabaseError(f"执行数据库查询失败：{exc}") from exc
    finally:
        db_cursor.close()
        conn.close()


@contextmanager
def transaction() -> Iterator:
    """提供自动提交或回滚的事务上下文。"""
    conn = get_connection()
    db_cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        yield db_cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        db_cursor.close()
        conn.close()


def reset_pool() -> None:
    """测试或配置切换时重置连接池。"""
    global _pool
    _pool = None


def sql_path(file_name: str) -> Path:
    """获取 SQL 脚本绝对路径。"""
    return PROJECT_ROOT / "sql" / file_name


def initialize_database_objects() -> None:
    """仅执行尚未应用的数据库迁移。"""
    conn = get_connection()
    db_cursor = conn.cursor()
    try:
        _ensure_migrations_table(db_cursor)
        conn.commit()
        applied = _get_applied_migrations(db_cursor)
        if not applied and _database_objects_are_ready(db_cursor):
            _record_baseline_migrations(db_cursor)
            conn.commit()
            applied.update(BASELINE_SCRIPTS)

        for script_name in MIGRATION_SCRIPTS:
            if script_name in applied:
                continue
            path = sql_path(script_name)
            content = path.read_text(encoding="utf-8")
            for statement in _split_sql_statements(content):
                db_cursor.execute(statement)
                while db_cursor.nextset():
                    pass
            if script_name == "01_app_tables.sql":
                _migrate_legacy_users_table(db_cursor)
                _migrate_legacy_logs_table(db_cursor)
            db_cursor.execute(
                """
                INSERT INTO scm_schema_migrations (migration_name)
                VALUES (%s)
                """,
                (script_name,),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        db_cursor.close()
        conn.close()


def _ensure_migrations_table(db_cursor) -> None:
    """创建轻量迁移记录表。"""
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scm_schema_migrations (
            migration_name VARCHAR(120) PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='SCM 应用数据库迁移记录'
        """
    )


def _get_applied_migrations(db_cursor) -> set[str]:
    db_cursor.execute("SELECT migration_name FROM scm_schema_migrations")
    return {row[0] for row in db_cursor.fetchall()}


def _database_objects_are_ready(db_cursor) -> bool:
    """判断旧版数据库是否已完整初始化，可直接建立迁移基线。"""
    checks = (
        ("TABLES", "TABLE_NAME", "scm_users"),
        ("TABLES", "TABLE_NAME", "scm_replenishment_orders"),
        ("VIEWS", "TABLE_NAME", "v_scm_inventory_status"),
        ("ROUTINES", "ROUTINE_NAME", "sp_scm_dashboard_kpis"),
        ("TRIGGERS", "TRIGGER_NAME", "trg_scm_users_after_insert"),
    )
    for source, column, object_name in checks:
        db_cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM information_schema.{source}
            WHERE {('TABLE_SCHEMA' if source in {'TABLES', 'VIEWS'} else 'ROUTINE_SCHEMA' if source == 'ROUTINES' else 'TRIGGER_SCHEMA')} = DATABASE()
                AND {column} = %s
            """,
            (object_name,),
        )
        if int(db_cursor.fetchone()[0]) == 0:
            return False
    return True


def _record_baseline_migrations(db_cursor) -> None:
    db_cursor.executemany(
        """
        INSERT IGNORE INTO scm_schema_migrations (migration_name)
        VALUES (%s)
        """,
        [(name,) for name in BASELINE_SCRIPTS],
    )


def _split_sql_statements(sql_content: str) -> list[str]:
    """按 MySQL DELIMITER 规则拆分 SQL 脚本。"""
    delimiter = ";"
    statements: list[str] = []
    buffer: list[str] = []

    for line in sql_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue

        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split(maxsplit=1)[1]
            continue

        buffer.append(line)
        if stripped.endswith(delimiter):
            statement = "\n".join(buffer)
            statement = statement[: -len(delimiter)].strip()
            if statement:
                statements.append(statement)
            buffer = []

    trailing = "\n".join(buffer).strip()
    if trailing:
        statements.append(trailing)
    return statements


def _migrate_legacy_users_table(db_cursor) -> None:
    """兼容旧版 scm_users 表结构。"""
    columns = _get_table_columns(db_cursor, "scm_users")
    if not columns:
        return

    if "password_hash" not in columns:
        db_cursor.execute(
            """
            ALTER TABLE scm_users
            ADD COLUMN password_hash CHAR(64) NULL COMMENT 'SHA2 密码摘要'
            AFTER username
            """
        )
        columns.add("password_hash")

    if "password" in columns:
        db_cursor.execute(
            """
            UPDATE scm_users
            SET password_hash = SHA2(password, 256)
            WHERE password_hash IS NULL OR password_hash = ''
            """
        )
        db_cursor.execute(
            """
            ALTER TABLE scm_users
            MODIFY password VARCHAR(100) NULL DEFAULT NULL
            COMMENT '旧版明文密码字段，已由 password_hash 替代'
            """
        )
    else:
        db_cursor.execute(
            """
            UPDATE scm_users
            SET password_hash = SHA2('123456', 256)
            WHERE password_hash IS NULL OR password_hash = ''
            """
        )

    migrations = {
        "display_name": (
            "ALTER TABLE scm_users "
            "ADD COLUMN display_name VARCHAR(80) NULL COMMENT '显示名称' "
            "AFTER password_hash"
        ),
        "is_active": (
            "ALTER TABLE scm_users "
            "ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1 "
            "COMMENT '是否启用' AFTER can_delete"
        ),
        "updated_at": (
            "ALTER TABLE scm_users "
            "ADD COLUMN updated_at TIMESTAMP NOT NULL "
            "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        ),
    }
    for column_name, statement in migrations.items():
        if column_name not in columns:
            db_cursor.execute(statement)
            columns.add(column_name)

    db_cursor.execute(
        """
        UPDATE scm_users
        SET display_name = username
        WHERE display_name IS NULL OR display_name = ''
        """
    )
    db_cursor.execute(
        """
        ALTER TABLE scm_users
        MODIFY password_hash CHAR(64) NOT NULL COMMENT 'SHA2 密码摘要'
        """
    )
    db_cursor.execute(
        """
        ALTER TABLE scm_users
        MODIFY display_name VARCHAR(80) NOT NULL COMMENT '显示名称'
        """
    )


def _get_table_columns(db_cursor, table_name: str) -> set[str]:
    """读取指定表的字段集合。"""
    db_cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
            AND table_name = %s
        """,
        (table_name,),
    )
    return {row[0] for row in db_cursor.fetchall()}


def _migrate_legacy_logs_table(db_cursor) -> None:
    """兼容旧版 scm_logs 表结构。"""
    columns = _get_table_columns(db_cursor, "scm_logs")
    if not columns:
        return

    if "created_at" not in columns:
        db_cursor.execute(
            """
            ALTER TABLE scm_logs
            ADD COLUMN created_at TIMESTAMP NOT NULL
            DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
            """
        )
        columns.add("created_at")

    if "log_time" in columns:
        db_cursor.execute(
            """
            UPDATE scm_logs
            SET created_at = log_time
            WHERE log_time IS NOT NULL
            """
        )
