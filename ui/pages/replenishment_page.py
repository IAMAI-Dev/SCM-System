# ui/pages/replenishment_page.py
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableView, QMessageBox
from service.auth_service import UserSession
from service.inventory_service import InventoryService
from ui.table_model import DictTableModel


class ReplenishmentPage(QWidget):
    """采购订单管理页面。"""

    def __init__(self, user_session: UserSession, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self.service = InventoryService(user_session)

        self.model = DictTableModel([
            ("order_id", "单号"),
            ("part_key", "零件ID"),
            ("supplier_key", "供应商ID"),
            ("quantity", "数量"),
            ("status", "状态"),
            ("created_at", "创建时间")
        ])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        toolbar = QHBoxLayout()
        title = QLabel("采购订单")
        title.setObjectName("page_title")
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.refresh()

    def refresh(self):
        try:
            rows = self.service.list_replenishment_orders()
            self.model.set_rows(rows)
        except Exception as e:
            QMessageBox.critical(self, "查询失败", str(e))
