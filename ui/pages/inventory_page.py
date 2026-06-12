"""库存调度页面。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from core.db import DatabaseError
from service.auth_service import UserSession
from service.inventory_service import InventoryService
from service.order_service import PermissionError
from ui.table_model import DictTableModel


class InventoryPage(QWidget):
    """库存调度页面。"""

    def __init__(self, user_session: UserSession, parent=None) -> None:
        super().__init__(parent)
        self.user_session = user_session
        self.service = InventoryService(user_session)
        self.model = DictTableModel(
            [
                ("part_key", "零件号"),
                ("part_name", "零件名称"),
                ("part_brand", "品牌"),
                ("supplier_key", "供应商ID"),
                ("supplier_name", "供应商"),
                ("avail_qty", "库存"),
                ("supply_cost", "成本"),
                ("stock_status", "状态"),
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
        self.low_only_check = QCheckBox("只看低库存")
        self.low_only_check.stateChanged.connect(self.refresh)
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh)
        replenish_button = QPushButton("补货")
        replenish_button.setObjectName("primary_button")
        replenish_button.clicked.connect(self.replenish)
        replenish_button.setEnabled(
            self.user_session.can_operate_module("inventory", "update")
        )
        abc_button = QPushButton("ABC 分类")
        abc_button.clicked.connect(self.show_abc)
        toolbar.addWidget(self.low_only_check)
        toolbar.addStretch(1)
        toolbar.addWidget(refresh_button)
        toolbar.addWidget(replenish_button)
        toolbar.addWidget(abc_button)
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
        """刷新库存列表。"""
        try:
            rows = self.service.list_inventory(
                low_only=self.low_only_check.isChecked()
            )
        except Exception as exc:
            self.status_label.setText(f"库存查询失败：{exc}")
            return
        self.model.set_rows(rows)
        self.status_label.setText(f"已加载 {len(rows)} 条库存记录。")

    def _selected_row(self) -> dict | None:
        """返回当前选中库存行。"""
        index = self.table.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "未选择", "请先选择一条库存记录。")
            return None
        return self.model.rows[index.row()]

    def replenish(self) -> None:
        """执行补货。"""
        row = self._selected_row()
        if not row:
            return
        quantity, ok = QInputDialog.getInt(
            self,
            "补货",
            "补货数量",
            100,
            1,
        )
        if not ok:
            return
        try:
            self.service.replenish(
                int(row["part_key"]),
                int(row["supplier_key"]),
                quantity,
            )
        except (PermissionError, DatabaseError, Exception) as exc:
            QMessageBox.critical(self, "补货失败", str(exc))
            return
        self.refresh()

    def show_abc(self) -> None:
        """展示 ABC 分类。"""
        try:
            result = self.service.classify_abc()
        except Exception as exc:
            QMessageBox.critical(self, "分类失败", str(exc))
            return
        QMessageBox.information(
            self,
            "ABC 库存分类",
            f"A 类：{result['A']}\nB 类：{result['B']}\nC 类：{result['C']}",
        )
