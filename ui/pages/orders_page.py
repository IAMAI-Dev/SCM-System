"""订单管理页面。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from core.db import DatabaseError
from service.auth_service import UserSession
from service.order_service import OrderService, PermissionError
from ui.table_model import DictTableModel


class OrdersPage(QWidget):
    """订单管理页面。"""

    def __init__(self, user_session: UserSession, parent=None) -> None:
        super().__init__(parent)
        self.service = OrderService(user_session)
        self.model = DictTableModel(
            [
                ("order_key", "订单号"),
                ("customer_name", "客户"),
                ("total_price", "总金额"),
                ("order_status", "状态"),
                ("order_date", "日期"),
                ("order_priority", "优先级"),
            ]
        )
        self._init_ui()
        self.refresh()

    def _init_ui(self) -> None:
        """初始化页面。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("订单号或客户名称")
        self.search_edit.returnPressed.connect(self.refresh)
        refresh_button = QPushButton("查询")
        refresh_button.clicked.connect(self.refresh)
        detail_button = QPushButton("查看明细")
        detail_button.clicked.connect(self.show_details)
        status_button = QPushButton("更新状态")
        status_button.clicked.connect(self.update_status)
        create_button = QPushButton("模拟下单")
        create_button.setObjectName("primary_button")
        create_button.clicked.connect(self.create_order)

        toolbar.addWidget(self.search_edit)
        toolbar.addWidget(refresh_button)
        toolbar.addWidget(detail_button)
        toolbar.addWidget(status_button)
        toolbar.addWidget(create_button)
        layout.addLayout(toolbar)

        self.status_label = QLabel("等待刷新")
        self.status_label.setObjectName("meta_label")
        layout.addWidget(self.status_label)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        """刷新订单列表。"""
        try:
            rows = self.service.list_orders(self.search_edit.text())
        except Exception as exc:
            self.status_label.setText(f"订单查询失败：{exc}")
            return
        self.model.set_rows(rows)
        self.status_label.setText(f"已加载 {len(rows)} 条订单。")

    def _selected_row(self) -> dict | None:
        """返回当前选中订单。"""
        index = self.table.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "未选择", "请先选择一条订单。")
            return None
        return self.model.rows[index.row()]

    def show_details(self) -> None:
        """展示订单明细。"""
        row = self._selected_row()
        if not row:
            return
        try:
            details = self.service.list_details(int(row["order_key"]))
        except Exception as exc:
            QMessageBox.critical(self, "查询失败", str(exc))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"订单 {row['order_key']} 明细")
        dialog.resize(880, 460)
        layout = QVBoxLayout(dialog)
        model = DictTableModel(
            [
                ("line_number", "行号"),
                ("part_key", "零件号"),
                ("part_name", "零件"),
                ("supplier_name", "供应商"),
                ("quantity", "数量"),
                ("extended_price", "金额"),
                ("line_status", "状态"),
            ],
            details,
        )
        table = QTableView()
        table.setAlternatingRowColors(True)
        table.setModel(model)
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)
        dialog.exec()

    def update_status(self) -> None:
        """更新订单状态。"""
        row = self._selected_row()
        if not row:
            return
        status, accepted = QInputDialog.getItem(
            self,
            "更新状态",
            "选择新状态",
            ["O", "F", "P"],
            0,
            False,
        )
        if not accepted:
            return
        try:
            self.service.update_status(int(row["order_key"]), status)
        except (PermissionError, DatabaseError, Exception) as exc:
            QMessageBox.critical(self, "更新失败", str(exc))
            return
        self.refresh()

    def create_order(self) -> None:
        """创建单行模拟订单。"""
        cust_key, ok = QInputDialog.getInt(self, "模拟下单", "客户ID")
        if not ok:
            return
        part_key, ok = QInputDialog.getInt(self, "模拟下单", "零件ID")
        if not ok:
            return
        supplier_key, ok = QInputDialog.getInt(self, "模拟下单", "供应商ID")
        if not ok:
            return
        quantity, ok = QInputDialog.getInt(
            self,
            "模拟下单",
            "订购数量",
            1,
            1,
        )
        if not ok:
            return

        try:
            new_key = self.service.create_order(
                cust_key,
                {
                    "part_key": part_key,
                    "supplier_key": supplier_key,
                    "quantity": quantity,
                },
            )
        except (PermissionError, ValueError, DatabaseError, Exception) as exc:
            QMessageBox.critical(self, "下单失败", str(exc))
            return

        QMessageBox.information(self, "下单成功", f"新订单号：{new_key}")
        self.refresh()
