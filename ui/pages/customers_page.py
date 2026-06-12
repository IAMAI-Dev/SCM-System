"""客户管理页面。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from service.auth_service import UserSession
from service.customer_service import CustomerService
from service.order_service import PermissionError
from ui.table_model import DictTableModel


class CustomersPage(QWidget):
    """客户管理页面。"""

    def __init__(self, user_session: UserSession, parent=None) -> None:
        super().__init__(parent)
        self.user_session = user_session
        self.service = CustomerService(user_session)
        self.model = DictTableModel(
            [
                ("customer_key", "客户ID"),
                ("customer_name", "客户名称"),
                ("nation_name", "国家"),
                ("phone", "电话"),
                ("account_balance", "余额"),
                ("order_count", "订单数"),
                ("total_revenue", "累计收入"),
            ]
        )
        self._init_ui()
        self.refresh()

    def _init_ui(self) -> None:
        """初始化页面。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("客户ID或名称")
        self.search_edit.returnPressed.connect(self.refresh)
        buttons = [
            ("查询", self.refresh, ""),
            ("新增", self.create_customer, "primary_button"),
            ("编辑", self.update_customer, ""),
            ("删除", self.delete_customer, ""),
        ]
        action_permissions = {
            "新增": "insert",
            "编辑": "update",
            "删除": "delete",
        }
        toolbar.addWidget(self.search_edit)
        for text, handler, object_name in buttons:
            button = QPushButton(text)
            if object_name:
                button.setObjectName(object_name)
            action = action_permissions.get(text)
            if action:
                button.setEnabled(
                    self.user_session.can_operate_module(
                        "customers",
                        action,
                    )
                )
            button.clicked.connect(handler)
            toolbar.addWidget(button)
        layout.addLayout(toolbar)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        """刷新客户列表。"""
        try:
            self.model.set_rows(
                self.service.list_customers(self.search_edit.text())
            )
        except Exception as exc:
            QMessageBox.critical(self, "查询失败", str(exc))

    def _selected_row(self) -> dict | None:
        """返回当前选中客户。"""
        index = self.table.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "未选择", "请先选择客户。")
            return None
        return self.model.rows[index.row()]

    def _collect_data(self, defaults: dict | None = None) -> dict | None:
        """通过输入框收集客户资料。"""
        defaults = defaults or {}
        name, ok = QInputDialog.getText(
            self,
            "客户名称",
            "客户名称",
            text=str(defaults.get("customer_name", "")),
        )
        if not ok:
            return None
        address, ok = QInputDialog.getText(self, "客户地址", "客户地址")
        if not ok:
            return None
        nation_key, ok = QInputDialog.getInt(self, "国家ID", "国家ID", 1)
        if not ok:
            return None
        phone, ok = QInputDialog.getText(
            self,
            "电话",
            "电话",
            text=str(defaults.get("phone", "")),
        )
        if not ok:
            return None
        balance, ok = QInputDialog.getDouble(
            self,
            "账户余额",
            "账户余额",
            float(defaults.get("account_balance") or 0),
        )
        if not ok:
            return None
        segment, ok = QInputDialog.getText(self, "市场分区", "市场分区")
        if not ok:
            return None
        return {
            "name": name,
            "address": address,
            "nation_key": nation_key,
            "phone": phone,
            "account_balance": balance,
            "market_segment": segment or "BUILDING",
            "comment": "Created by SCM desktop",
        }

    def create_customer(self) -> None:
        """新增客户。"""
        data = self._collect_data()
        if not data:
            return
        try:
            cust_key = self.service.create_customer(data)
        except (PermissionError, Exception) as exc:
            QMessageBox.critical(self, "新增失败", str(exc))
            return
        QMessageBox.information(self, "新增成功", f"客户ID：{cust_key}")
        self.refresh()

    def update_customer(self) -> None:
        """编辑客户。"""
        row = self._selected_row()
        if not row:
            return
        data = self._collect_data(row)
        if not data:
            return
        try:
            self.service.update_customer(int(row["customer_key"]), data)
        except (PermissionError, Exception) as exc:
            QMessageBox.critical(self, "编辑失败", str(exc))
            return
        self.refresh()

    def delete_customer(self) -> None:
        """删除客户。"""
        row = self._selected_row()
        if not row:
            return
        if QMessageBox.question(self, "确认", "确定删除该客户吗？") != (
            QMessageBox.StandardButton.Yes
        ):
            return
        try:
            self.service.delete_customer(int(row["customer_key"]))
        except (PermissionError, Exception) as exc:
            QMessageBox.critical(self, "删除失败", str(exc))
            return
        self.refresh()
