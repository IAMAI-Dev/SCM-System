"""库存业务服务。"""

from __future__ import annotations

from core.db import transaction
from dao import auth_dao, inventory_dao
from service.auth_service import UserSession
from service.order_service import PermissionError


class InventoryService:
    """库存服务。"""

    def __init__(self, user_session: UserSession) -> None:
        self.user_session = user_session

    def list_inventory(self, low_only: bool = False) -> list[dict]:
        """查询库存。"""
        self._require("view")
        return inventory_dao.list_inventory(low_only=low_only)

    def replenish(
        self,
        part_key: int,
        supplier_key: int,
        quantity: int,
    ) -> None:
        """执行补货。"""
        self._require("update")
        part_key = int(part_key)
        supplier_key = int(supplier_key)
        quantity = int(quantity)
        if part_key <= 0 or supplier_key <= 0:
            raise ValueError("零件ID和供应商ID必须大于 0。")
        if quantity <= 0:
            raise ValueError("补货数量必须大于 0。")

        with transaction() as db_cursor:
            inventory_dao.replenish(
                part_key,
                supplier_key,
                quantity,
                db_cursor=db_cursor,
            )
            auth_dao.log_action(
                self.user_session.username,
                "inventory",
                "UPDATE",
                f"零件 {part_key} 供应商 {supplier_key} 补货 {quantity}",
                db_cursor=db_cursor,
            )

    def classify_abc(self) -> dict[str, int]:
        """执行 ABC 库存分类。"""
        self._require("view")
        rows = inventory_dao.list_stock_values()
        total_value = sum(float(row["stock_value"] or 0) for row in rows)
        if total_value <= 0:
            return {"A": 0, "B": 0, "C": 0}

        result = {"A": 0, "B": 0, "C": 0}
        cumulative = 0.0
        for row in rows:
            cumulative += float(row["stock_value"] or 0)
            ratio = cumulative / total_value
            if ratio <= 0.7:
                result["A"] += 1
            elif ratio <= 0.9:
                result["B"] += 1
            else:
                result["C"] += 1
        return result

    def get_replenish_suggestions(self) -> list[dict]:
        """生成智能补货建议：返回库存低于100的零件及其建议补货量。"""
        self._require("view")
        all_inventory = self.list_inventory(low_only=False)
        suggestions = []
        for item in all_inventory:
            current_qty = int(item.get("avail_qty") or 0)
            if current_qty < 100:
                suggestions.append({
                    "part_key": item.get("part_key"),
                    "part_name": item.get("part_name"),
                    "supplier_name": item.get("supplier_name"),
                    "avail_qty": current_qty,
                    "suggest_qty": 100 - current_qty,
                })
        return suggestions

    def list_replenishment_orders(self) -> list[dict]:
        """列出所有补货订单。"""
        self._require("view")
        return inventory_dao.list_replenishment_orders()

    def create_replenishment_order(
        self,
        part_key: int,
        supplier_key: int,
        quantity: int,
    ) -> int:
        """创建补货订单。"""
        self._require("update")
        part_key = int(part_key)
        supplier_key = int(supplier_key)
        quantity = int(quantity)
        if part_key <= 0 or supplier_key <= 0:
            raise ValueError("零件ID和供应商ID必须大于0")
        if quantity <= 0:
            raise ValueError("补货数量必须大于0")
        with transaction() as db_cursor:
            order_id = inventory_dao.create_replenishment_order(
                part_key, supplier_key, quantity, db_cursor
            )
            auth_dao.log_action(
                self.user_session.username,
                "inventory",
                "INSERT",
                f"创建补货订单 {order_id}: 零件 {part_key} 供应商 {supplier_key} 数量 {quantity}",
                db_cursor=db_cursor,
            )
            return order_id

    def _require(self, action: str) -> None:
        """检查采购模块权限。"""
        if not self.user_session.can_operate_module("inventory", action):
            raise PermissionError("当前用户没有库存模块操作权限。")
