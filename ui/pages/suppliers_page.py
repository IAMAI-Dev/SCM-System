"""供应商分析页面。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from service.supplier_service import SupplierService
from ui.table_model import DictTableModel


class SuppliersPage(QWidget):
    """供应商分析页面。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.service = SupplierService()
        self.model = DictTableModel(
            [
                ("supplier_key", "供应商ID"),
                ("supplier_name", "供应商"),
                ("nation_name", "国家"),
                ("part_count", "供应零件数"),
                ("avg_supply_cost", "平均成本"),
                ("total_available_qty", "总库存"),
            ]
        )
        self._init_ui()
        self.refresh()

    def _init_ui(self) -> None:
        """初始化页面。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        toolbar = QHBoxLayout()
        toolbar.addStretch(1)
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_button)
        layout.addLayout(toolbar)

        table = QTableView()
        table.setAlternatingRowColors(True)
        table.setModel(self.model)
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table, 1)

    def refresh(self) -> None:
        """刷新供应商列表。"""
        try:
            self.model.set_rows(self.service.list_suppliers())
        except Exception as exc:
            QMessageBox.critical(self, "查询失败", str(exc))
