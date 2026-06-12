"""订单业务服务。"""

from __future__ import annotations

from core.db import transaction
from dao import auth_dao, order_dao
from service.auth_service import UserSession


class PermissionError(RuntimeError):
    """权限不足异常。"""


class OrderService:
    """订单服务。"""

    VALID_STATUSES = {"O", "F", "P"}

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
        status = str(status).strip().upper()
        if status not in self.VALID_STATUSES:
            raise ValueError("订单状态只能是 O、F 或 P。")

        with transaction() as db_cursor:
            changed = order_dao.update_order_status(
                order_key,
                status,
                db_cursor=db_cursor,
            )
            if changed:
                auth_dao.log_action(
                    self.user_session.username,
                    "orders",
                    "UPDATE",
                    f"订单 {order_key} 状态更新为 {status}",
                    db_cursor=db_cursor,
                )

    def create_order(self, cust_key: int, item: dict) -> int:
        """创建单行模拟订单。"""
        self._require("insert")
        cust_key = int(cust_key)
        normalized_item = self._normalize_item(item)
        if cust_key <= 0:
            raise ValueError("客户ID必须大于 0。")

        with transaction() as db_cursor:
            new_order_key = order_dao.create_order(
                cust_key,
                [normalized_item],
                db_cursor=db_cursor,
            )
            auth_dao.log_action(
                self.user_session.username,
                "orders",
                "INSERT",
                f"创建订单 {new_order_key}",
                db_cursor=db_cursor,
            )
        return new_order_key

    def _require(self, action: str) -> None:
        """检查销售模块权限。"""
        if not self.user_session.can_operate_module("orders", action):
            raise PermissionError("当前用户没有订单模块操作权限。")

    def _normalize_item(self, item: dict) -> dict:
        """校验并标准化订单行。"""
        part_key = int(item.get("part_key") or 0)
        supplier_key = int(item.get("supplier_key") or 0)
        quantity = int(item.get("quantity") or 0)
        if part_key <= 0 or supplier_key <= 0:
            raise ValueError("零件ID和供应商ID必须大于 0。")
        if quantity <= 0:
            raise ValueError("订购数量必须大于 0。")
        return {
            "part_key": part_key,
            "supplier_key": supplier_key,
            "quantity": quantity,
        }
