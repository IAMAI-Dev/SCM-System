"""客户业务服务。"""

from __future__ import annotations

from dao import auth_dao, customer_dao
from service.auth_service import UserSession
from service.order_service import PermissionError


class CustomerService:
    """客户服务。"""

    def __init__(self, user_session: UserSession) -> None:
        self.user_session = user_session

    def list_customers(self, search_key: str = "") -> list[dict]:
        """查询客户。"""
        return customer_dao.list_customers(search_key.strip())

    def create_customer(self, data: dict) -> int:
        """新增客户。"""
        self._require("insert")
        cust_key = customer_dao.create_customer(data)
        auth_dao.log_action(
            self.user_session.username,
            "customers",
            "INSERT",
            f"新增客户 {cust_key}",
        )
        return cust_key

    def update_customer(self, cust_key: int, data: dict) -> None:
        """更新客户。"""
        self._require("update")
        customer_dao.update_customer(cust_key, data)
        auth_dao.log_action(
            self.user_session.username,
            "customers",
            "UPDATE",
            f"更新客户 {cust_key}",
        )

    def delete_customer(self, cust_key: int) -> None:
        """删除客户。"""
        self._require("delete")
        customer_dao.delete_customer(cust_key)
        auth_dao.log_action(
            self.user_session.username,
            "customers",
            "DELETE",
            f"删除客户 {cust_key}",
        )

    def _require(self, action: str) -> None:
        """检查权限。"""
        if not self.user_session.has_permission(action):
            raise PermissionError("当前用户没有客户模块操作权限。")
