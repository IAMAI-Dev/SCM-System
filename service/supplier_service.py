"""供应商业务服务。"""

from __future__ import annotations

from dao import supplier_dao


class SupplierService:
    """供应商服务。"""

    def list_suppliers(self) -> list[dict]:
        """查询供应商表现。"""
        return supplier_dao.list_suppliers()
