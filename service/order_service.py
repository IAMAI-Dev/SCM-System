"""订单业务服务。"""

from __future__ import annotations

from dao import auth_dao, order_dao
from service.auth_service import UserSession


class PermissionError(RuntimeError):
    """权限不足异常。"""


class OrderService:
    """订单服务。"""

    def __init__(self, user_session: UserSession) -> None:
        self.user_session = user_session

    def list_orders(self, search_key: str = "") -> list[dict]:
        """查询订单列表。"""
        self._require("view")
        return order_dao.list_orders(search_key=search_key.strip())

    def list_details(self, order_key: int) -> list[dict]:
        """查询订单明细。"""
        self._require("view")
        return order_dao.list_order_details(order_key)

    def update_status(self, order_key: int, status: str) -> None:
        """更新订单状态。"""
        self._require("update")
        order_dao.update_order_status(order_key, status)
        auth_dao.log_action(
            self.user_session.username,
            "orders",
            "UPDATE",
            f"订单 {order_key} 状态更新为 {status}",
        )

    def create_order(self, cust_key: int, item: dict) -> int:
        """创建单行模拟订单。"""
        self._require("insert")
        new_order_key = order_dao.create_order(cust_key, [item])
        auth_dao.log_action(
            self.user_session.username,
            "orders",
            "INSERT",
            f"创建订单 {new_order_key}",
        )
        return new_order_key

    def _require(self, action: str) -> None:
        """检查销售模块权限。"""
        if not self.user_session.can_operate_module("orders", action):
            raise PermissionError("当前用户没有订单模块操作权限。")
