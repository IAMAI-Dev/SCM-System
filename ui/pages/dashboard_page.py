# ui/pages/dashboard_page.py
from __future__ import annotations

from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from service.dashboard_service import DashboardService, KpiItem
from ui.table_model import DictTableModel


class DashboardWorker(QObject):
    """后台加载总览仪表盘数据。"""

    loaded = Signal(object)
    failed = Signal(str)

    def run(self) -> None:
        try:
            data = DashboardService().load_dashboard()
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.loaded.emit(data)


class DashboardPage(QWidget):
    """供应链总览仪表盘。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.load_state = "idle"
        self._has_data = False
        self._load_thread: QThread | None = None
        self._load_worker: DashboardWorker | None = None
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
        QTimer.singleShot(0, self.refresh)

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
        self.refresh_button = refresh_button

        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loading_bar")
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setFixedWidth(140)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setVisible(False)

        export_button = QPushButton("导出 Excel")
        export_button.clicked.connect(self.export_to_excel)

        action_layout.addWidget(title)
        action_layout.addStretch(1)
        action_layout.addWidget(self.loading_bar)
        action_layout.addWidget(refresh_button)
        action_layout.addWidget(export_button)
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

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setModel(self.low_stock_model)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

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
        if self._load_thread is not None:
            return

        self.load_state = "loading"
        self.refresh_button.setEnabled(False)
        self.loading_bar.setVisible(True)
        self.status_label.setText("正在加载仪表盘数据...")

        self._load_thread = QThread(self)
        self._load_worker = DashboardWorker()
        self._load_worker.moveToThread(self._load_thread)
        self._load_thread.started.connect(self._load_worker.run)
        self._load_worker.loaded.connect(self._handle_loaded)
        self._load_worker.failed.connect(self._handle_failed)
        self._load_worker.loaded.connect(self._load_thread.quit)
        self._load_worker.failed.connect(self._load_thread.quit)
        self._load_worker.loaded.connect(self._load_worker.deleteLater)
        self._load_worker.failed.connect(self._load_worker.deleteLater)
        self._load_thread.finished.connect(self._load_thread.deleteLater)
        self._load_thread.finished.connect(self._clear_loader)
        self._load_thread.start()

    def _handle_loaded(self, data: tuple) -> None:
        kpis, sales_history, low_stock = data

        self._apply_kpis(kpis)
        self.low_stock_model.set_rows(low_stock)
        self._has_data = True
        self.load_state = "loaded"
        self.refresh_button.setEnabled(True)
        self.loading_bar.setVisible(False)
        self.status_label.setText(
            f"已刷新，趋势月份 {len(sales_history)} 个，"
            f"库存预警 {len(low_stock)} 条。"
        )

    def _handle_failed(self, message: str) -> None:
        self.load_state = "error"
        self.refresh_button.setEnabled(True)
        self.loading_bar.setVisible(False)
        prefix = "刷新失败" if self._has_data else "加载失败"
        self.status_label.setText(f"{prefix}：{message}")

    def _clear_loader(self) -> None:
        self._load_thread = None
        self._load_worker = None

    def closeEvent(self, event) -> None:
        if self._load_thread is not None and self._load_thread.isRunning():
            self._load_thread.quit()
            self._load_thread.wait(3000)
        super().closeEvent(event)

    def _apply_kpis(self, kpis: list[KpiItem]) -> None:
        """更新 KPI 文案。"""
        for labels, kpi in zip(self.kpi_labels, kpis):
            title, value, trend = labels
            title.setText(kpi.title)
            value.setText(kpi.value)
            trend.setText(kpi.trend)

    def export_to_excel(self):
        """一键导出低库存预警表格数据为 Excel"""
        from utils.excel_exporter import export_table_view_to_excel

        export_table_view_to_excel(self.table, "低库存预警报表", self)
