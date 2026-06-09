"""库存业务服务。"""

from __future__ import annotations

from dao import auth_dao, inventory_dao
from service.auth_service import UserSession
from service.order_service import PermissionError


class InventoryService:
    """库存服务。"""

    def __init__(self, user_session: UserSession) -> None:
        self.user_session = user_session

    def list_inventory(self, low_only: bool = False) -> list[dict]:
        """查询库存。"""
        return inventory_dao.list_inventory(low_only=low_only)

    def replenish(
        self,
        part_key: int,
        supplier_key: int,
        quantity: int,
    ) -> None:
        """执行补货。"""
        if not self.user_session.has_permission("update"):
            raise PermissionError("当前用户没有补货权限。")
        inventory_dao.replenish(part_key, supplier_key, quantity)
        auth_dao.log_action(
            self.user_session.username,
            "inventory",
            "UPDATE",
            f"零件 {part_key} 供应商 {supplier_key} 补货 {quantity}",
        )

    def classify_abc(self) -> dict[str, int]:
        """执行 ABC 库存分类。"""
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
