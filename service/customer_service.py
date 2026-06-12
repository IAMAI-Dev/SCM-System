"""客户业务服务。"""

from __future__ import annotations

from core.db import transaction
from dao import auth_dao, customer_dao
from service.auth_service import UserSession
from service.order_service import PermissionError


class CustomerService:
    """客户服务。"""

    def __init__(self, user_session: UserSession) -> None:
        self.user_session = user_session

    def list_customers(self, search_key: str = "") -> list[dict]:
        """查询客户。"""
        self._require("view")
        return customer_dao.list_customers(search_key.strip())

    def create_customer(self, data: dict) -> int:
        """新增客户。"""
        self._require("insert")
        normalized = self._normalize_customer_data(data)
        with transaction() as db_cursor:
            cust_key = customer_dao.create_customer(
                normalized,
                db_cursor=db_cursor,
            )
            auth_dao.log_action(
                self.user_session.username,
                "customers",
                "INSERT",
                f"新增客户 {cust_key}",
                db_cursor=db_cursor,
            )
        return cust_key

    def update_customer(self, cust_key: int, data: dict) -> None:
        """更新客户。"""
        self._require("update")
        normalized = self._normalize_customer_data(data)
        with transaction() as db_cursor:
            customer_dao.update_customer(
                cust_key,
                normalized,
                db_cursor=db_cursor,
            )
            auth_dao.log_action(
                self.user_session.username,
                "customers",
                "UPDATE",
                f"更新客户 {cust_key}",
                db_cursor=db_cursor,
            )

    def delete_customer(self, cust_key: int) -> None:
        """删除客户。"""
        self._require("delete")
        with transaction() as db_cursor:
            customer_dao.delete_customer(cust_key, db_cursor=db_cursor)
            auth_dao.log_action(
                self.user_session.username,
                "customers",
                "DELETE",
                f"删除客户 {cust_key}",
                db_cursor=db_cursor,
            )

    def _require(self, action: str) -> None:
        """检查客户管理模块权限。"""
        if not self.user_session.can_operate_module("customers", action):
            raise PermissionError("当前用户没有客户模块操作权限。")

    def _normalize_customer_data(self, data: dict) -> dict:
        """校验并标准化客户资料。"""
        name = str(data.get("name", "")).strip()
        address = str(data.get("address", "")).strip()
        phone = str(data.get("phone", "")).strip()
        market_segment = str(
            data.get("market_segment") or "BUILDING"
        ).strip()
        comment = str(data.get("comment") or "").strip()

        if not name:
            raise ValueError("客户名称不能为空。")
        if not address:
            raise ValueError("客户地址不能为空。")
        if not phone:
            raise ValueError("客户电话不能为空。")

        nation_key = int(data.get("nation_key") or 0)
        if nation_key <= 0:
            raise ValueError("国家ID必须大于 0。")

        return {
            "name": name,
            "address": address,
            "nation_key": nation_key,
            "phone": phone,
            "account_balance": float(data.get("account_balance") or 0),
            "market_segment": market_segment or "BUILDING",
            "comment": comment or "Created by SCM desktop",
        }
