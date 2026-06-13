"""应用配置读取模块。"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.ini"


@dataclass(frozen=True)
class DatabaseConfig:
    """数据库连接配置。"""

    host: str
    port: int
    user: str
    password: str
    database: str
    pool_name: str
    pool_size: int


@dataclass(frozen=True)
class AppConfig:
    """应用运行配置。"""

    warehouse: str
    account_set: str
    theme: str


def _load_parser() -> configparser.ConfigParser:
    """读取本地配置文件。"""
    parser = configparser.ConfigParser()
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as file_obj:
            parser.read_file(file_obj)
    return parser


def load_database_config() -> DatabaseConfig:
    """加载数据库配置，环境变量优先于配置文件。"""
    parser = _load_parser()
    return DatabaseConfig(
        host=os.getenv(
            "SCM_DB_HOST",
            parser.get("database", "host", fallback="localhost"),
        ),
        port=int(
            os.getenv(
                "SCM_DB_PORT",
                parser.get("database", "port", fallback="3306"),
            )
        ),
        user=os.getenv(
            "SCM_DB_USER",
            parser.get("database", "user", fallback="root"),
        ),
        password=os.getenv(
            "SCM_DB_PASSWORD",
            parser.get("database", "password", fallback=""),
        ),
        database=os.getenv(
            "SCM_DB_NAME",
            parser.get("database", "database", fallback="experiment2026"),
        ),
        pool_name=os.getenv(
            "SCM_DB_POOL_NAME",
            parser.get("database", "pool_name", fallback="scm_pool"),
        ),
        pool_size=int(
            os.getenv(
                "SCM_DB_POOL_SIZE",
                parser.get("database", "pool_size", fallback="5"),
            )
        ),
    )


def load_app_config() -> AppConfig:
    """加载界面展示配置。"""
    parser = _load_parser()
    database_name = os.getenv(
        "SCM_DB_NAME",
        parser.get("database", "database", fallback="experiment2026"),
    )
    return AppConfig(
        warehouse=parser.get("app", "warehouse", fallback="华东总仓"),
        account_set=os.getenv(
            "SCM_ACCOUNT_SET",
            os.getenv(
                "SCM_DB_NAME",
                parser.get("app", "account_set", fallback=database_name),
            ),
        ),
        theme=parser.get("app", "theme", fallback="industrial"),
    )
