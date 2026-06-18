"""经营分析业务服务。"""

from __future__ import annotations

from core.db import cursor as db_cursor_ctx
from dao import manager_dao
from service.order_service import PermissionError


class ManagerService:
    """经理经营分析服务。"""

    def __init__(self, user_session) -> None:
        self.user_session = user_session

    def load_analysis(self) -> dict[str, list[dict]]:
        """加载经营分析数据（复用单连接减少连接池开销）。"""
        if not self.user_session.is_manager:
            raise PermissionError("仅经理可查看经营分析")

        return {
            "monthly_revenue": manager_dao.get_monthly_revenue(),
            "top_parts": manager_dao.get_top_parts(),
            "customer_value": manager_dao.get_customer_value(),
        }
