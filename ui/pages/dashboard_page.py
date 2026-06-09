"""总览仪表盘页面。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from core.db import DatabaseError
from service.dashboard_service import DashboardService, KpiItem
from ui.table_model import DictTableModel


class DashboardPage(QWidget):
    """供应链总览仪表盘。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.service = DashboardService()
        self.kpi_labels: list[tuple[QLabel, QLabel, QLabel]] = []
        self.low_stock_model = DictTableModel(
            [
                ("part_key", "零件号"),
                ("part_name", "零件名称"),
                ("supplier_name", "供应商"),
                ("avail_qty", "库存量"),
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
        layout.setSpacing(14)

        action_layout = QHBoxLayout()
        title = QLabel("供应链运行概览")
        title.setObjectName("page_title")
        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primary_button")
        refresh_button.clicked.connect(self.refresh)
        action_layout.addWidget(title)
        action_layout.addStretch(1)
        action_layout.addWidget(refresh_button)
        layout.addLayout(action_layout)

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(10)
        layout.addLayout(self.kpi_grid)
        self._build_kpi_cards()

        self.status_label = QLabel("等待刷新")
        self.status_label.setObjectName("meta_label")
        layout.addWidget(self.status_label)

        table_title = QLabel("低库存与预警快照")
        table_title.setObjectName("page_title")
        layout.addWidget(table_title)

        table = QTableView()
        table.setAlternatingRowColors(True)
        table.setModel(self.low_stock_model)
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table, 1)

    def _build_kpi_cards(self) -> None:
        """构建 KPI 卡片。"""
        for index in range(4):
            card = QFrame()
            card.setObjectName("content_panel")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)

            title = QLabel("--")
            title.setObjectName("meta_label")
            value = QLabel("0")
            value.setStyleSheet(
                "font-size: 20pt; font-weight: 700; "
                "color: #252525; background: transparent;"
            )
            trend = QLabel("--")
            trend.setObjectName("meta_label")
            card_layout.addWidget(title)
            card_layout.addWidget(value)
            card_layout.addWidget(trend)
            self.kpi_labels.append((title, value, trend))
            self.kpi_grid.addWidget(card, 0, index)

    def refresh(self) -> None:
        """刷新仪表盘数据。"""
        try:
            kpis, sales_history, low_stock = self.service.load_dashboard()
        except DatabaseError as exc:
            self.status_label.setText(str(exc))
            return
        except Exception as exc:
            self.status_label.setText(f"刷新失败：{exc}")
            return

        self._apply_kpis(kpis)
        self.low_stock_model.set_rows(low_stock)
        self.status_label.setText(
            f"已刷新，趋势月份 {len(sales_history)} 个，"
            f"库存预警 {len(low_stock)} 条。"
        )

    def _apply_kpis(self, kpis: list[KpiItem]) -> None:
        """更新 KPI 文案。"""
        for labels, kpi in zip(self.kpi_labels, kpis):
            title, value, trend = labels
            title.setText(kpi.title)
            value.setText(kpi.value)
            trend.setText(kpi.trend)
