
from __future__ import annotations
"""供应商分析页面。"""



from PySide6.QtCore import (
    QObject,
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QAbstractItemView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from service.auth_service import UserSession
from service.supplier_service import SupplierKpi, SupplierService
from ui.analytics_widgets import FadeFrame, LoadingChart, chart_card
from matplotlib.figure import Figure


class SupplierAnalysisWorker(QObject):
    """后台加载供应商分析数据。"""

    loaded = Signal(object)
    failed = Signal(str)

    def __init__(self, user_session: UserSession) -> None:
        super().__init__()
        self.user_session = user_session

    def run(self) -> None:
        """执行耗时数据库查询。"""
        try:
            analysis = SupplierService(self.user_session).load_analysis()
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.loaded.emit(analysis)


class SuppliersPage(QWidget):
    """供应商分析页面。"""

    def __init__(
        self,
        user_session: UserSession,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.user_session = user_session
        self.kpi_labels: list[tuple[QLabel, QLabel, QLabel]] = []
        self.kpi_cards: list[FadeFrame] = []
        self._load_thread: QThread | None = None
        self._load_worker: SupplierAnalysisWorker | None = None
        self.load_state = "idle"
        self._has_data = False
        self._init_ui()
        QTimer.singleShot(0, self.refresh)

    def _init_ui(self) -> None:
        """初始化页面。"""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        toolbar = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("供应商分析")
        title.setObjectName("page_title")
        subtitle = QLabel("供应商绩效评估与采购数据可视化")
        subtitle.setObjectName("meta_label")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        self.status_label = QLabel("等待加载")
        self.status_label.setObjectName("meta_label")
        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loading_bar")
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setFixedWidth(140)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setVisible(False)
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("primary_button")
        self.refresh_button.clicked.connect(self.refresh)

        export_button = QPushButton("导出 Excel")
        export_button.clicked.connect(self.export_to_excel)


        toolbar.addLayout(title_box)
        toolbar.addStretch(1)
        toolbar.addWidget(self.status_label)
        toolbar.addWidget(self.loading_bar)
        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(export_button)
        layout.addLayout(toolbar)

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(10)
        layout.addLayout(self.kpi_grid)
        self._build_kpi_cards()

        self.chart_grid = QGridLayout()
        self.chart_grid.setSpacing(14)

        self.bar_chart = LoadingChart(Figure(figsize=(7.0, 3.0), dpi=85))
        self.donut_chart = LoadingChart(Figure(figsize=(4.8, 3.0), dpi=85))
        self.line_chart = LoadingChart(Figure(figsize=(5.0, 3.0), dpi=85))

        self.bar_card = chart_card(
            "各供应商供应量对比",
            self.bar_chart,
        )
        self.donut_card = chart_card(
            "供应商国家分布",
            self.donut_chart,
        )
        self.line_card = chart_card(
            "采购额趋势（万元）",
            self.line_chart,
        )
        self.rank_card = self._build_rank_card()
        self._compact_chart_layout: bool | None = None
        self._relayout_charts(compact=False)
        layout.addLayout(self.chart_grid)

    def resizeEvent(self, event) -> None:
        """窄窗口改为单列图表，避免图例区域被压缩。"""
        super().resizeEvent(event)
        compact = event.size().width() < 900
        self._relayout_kpis(compact)
        self._relayout_charts(compact)

    def _relayout_kpis(self, compact: bool) -> None:
        for card in self.kpi_cards:
            self.kpi_grid.removeWidget(card)
        columns = 2 if compact else 4
        for index, card in enumerate(self.kpi_cards):
            self.kpi_grid.addWidget(
                card,
                index // columns,
                index % columns,
            )

    def _relayout_charts(self, compact: bool) -> None:
        if self._compact_chart_layout == compact:
            return
        self._compact_chart_layout = compact
        for card in (
            self.bar_card,
            self.donut_card,
            self.line_card,
            self.rank_card,
        ):
            self.chart_grid.removeWidget(card)

        if compact:
            self.chart_grid.addWidget(self.bar_card, 0, 0, 1, 3)
            self.chart_grid.addWidget(self.donut_card, 1, 0, 1, 3)
            self.chart_grid.addWidget(self.line_card, 2, 0, 1, 3)
            self.chart_grid.addWidget(self.rank_card, 3, 0, 1, 3)
        else:
            self.chart_grid.addWidget(self.bar_card, 0, 0, 1, 2)
            self.chart_grid.addWidget(self.donut_card, 0, 2)
            self.chart_grid.addWidget(self.line_card, 1, 0)
            self.chart_grid.addWidget(self.rank_card, 1, 1, 1, 2)
        for column in range(3):
            self.chart_grid.setColumnStretch(column, 2)

    def _build_kpi_cards(self) -> None:
        """构建 KPI 卡片。"""
        for index in range(4):
            card = FadeFrame()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            label = QLabel("--")
            label.setObjectName("meta_label")
            value = QLabel("0")
            value.setObjectName("kpi_value")
            hint = QLabel("--")
            hint.setObjectName("meta_label")
            card_layout.addWidget(label)
            card_layout.addWidget(value)
            card_layout.addWidget(hint)
            self.kpi_labels.append((label, value, hint))
            self.kpi_cards.append(card)
            self.kpi_grid.addWidget(card, 0, index)

    def _build_rank_card(self) -> FadeFrame:
        """构建供应商排行卡片。"""
        card = FadeFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        title = QLabel("供应商排行")
        title.setObjectName("section_title")
        layout.addWidget(title)

        self.rank_table = QTableWidget(0, 5)
        self.rank_table.setHorizontalHeaderLabels(
            ["供应商", "国家", "供应件数", "评分", "趋势"]
        )
        self.rank_table.verticalHeader().setVisible(False)
        self.rank_table.setAlternatingRowColors(True)
        self.rank_table.horizontalHeader().setStretchLastSection(True)
        self.rank_table.setMinimumHeight(245)
        self.rank_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self.rank_table, 1)
        return card

    def refresh(self) -> None:
        """刷新供应商分析数据。"""
        if self._load_thread is not None:
            return

        self._set_loading(True)
        self._load_thread = QThread(self)
        self._load_worker = SupplierAnalysisWorker(self.user_session)
        self._load_worker.moveToThread(self._load_thread)
        self._load_thread.started.connect(self._load_worker.run)
        self._load_worker.loaded.connect(self._handle_analysis_loaded)
        self._load_worker.failed.connect(self._handle_analysis_failed)
        self._load_worker.loaded.connect(self._load_thread.quit)
        self._load_worker.failed.connect(self._load_thread.quit)
        self._load_worker.loaded.connect(self._load_worker.deleteLater)
        self._load_worker.failed.connect(self._load_worker.deleteLater)
        self._load_thread.finished.connect(self._load_thread.deleteLater)
        self._load_thread.finished.connect(self._clear_loader)
        self._load_thread.start()

    def _handle_analysis_loaded(self, analysis: dict) -> None:
        """应用后台加载结果。"""
        self._apply_kpis(analysis["kpis"])
        self._apply_ranking(analysis["ranking"])
        self.status_label.setText("正在渲染图表...")
        QTimer.singleShot(
            0,
            lambda: self._render_chart(
                self.bar_chart,
                "draw_bar",
                analysis["bar_data"],
            ),
        )
        QTimer.singleShot(
            60,
            lambda: self._render_chart(
                self.donut_chart,
                "draw_donut",
                analysis["country_data"],
            ),
        )
        QTimer.singleShot(
            120,
            lambda: self._render_chart(
                self.line_chart,
                "draw_line",
                analysis["trend_data"],
                final=True,
            ),
        )

    def _render_chart(
        self,
        chart: LoadingChart,
        method_name: str,
        rows: list[dict],
        final: bool = False,
    ) -> None:
        """分批完成单次绘图，避免连续绘制阻塞事件循环。"""
        getattr(chart.canvas, method_name)(rows)
        chart.show_chart()
        if final:
            self._has_data = True
            self.load_state = "loaded"
            self._set_loading(False)
            self.status_label.setText("已加载供应商分析数据")

    def _handle_analysis_failed(self, message: str) -> None:
        """显示后台加载错误。"""
        first_load = not self._has_data
        self.load_state = "error"
        self._set_loading(False)
        self.status_label.setText("供应商分析加载失败")
        if first_load:
            for chart in (self.bar_chart, self.donut_chart, self.line_chart):
                chart.set_error("图表数据加载失败")
        QMessageBox.critical(self, "查询失败", message)

    def _clear_loader(self) -> None:
        """清理后台加载对象引用。"""
        self._load_thread = None
        self._load_worker = None

    def closeEvent(self, event) -> None:
        """关闭页面时等待后台加载线程结束。"""
        if self._load_thread is not None and self._load_thread.isRunning():
            self._load_thread.quit()
            self._load_thread.wait(3000)
        super().closeEvent(event)

    def _set_loading(self, loading: bool) -> None:
        """切换加载状态。"""
        self.refresh_button.setEnabled(not loading)
        self.loading_bar.setVisible(loading)
        if loading:
            if not self._has_data:
                for chart in (self.bar_chart, self.donut_chart, self.line_chart):
                    chart.set_loading()
            self.load_state = "loading"
            self.status_label.setText("正在加载供应商分析...")

    def _apply_kpis(self, kpis: list[SupplierKpi]) -> None:
        """更新 KPI 文案。"""
        for labels, kpi in zip(self.kpi_labels, kpis):
            label, value, hint = labels
            label.setText(kpi.label)
            value.setText(kpi.value)
            hint.setText(kpi.hint)

    def _apply_ranking(self, rows: list[dict]) -> None:
        """更新供应商排行表。"""
        self.rank_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self._set_item(row_index, 0, self._rank_name(row_index, row))
            self._set_item(row_index, 1, row["nation_name"])
            self._set_item(row_index, 2, str(row["part_count"]))
            self._set_item(row_index, 3, str(row["score"]))
            self.rank_table.setCellWidget(
                row_index,
                3,
                self._score_bar(int(row["score"])),
            )
            self._set_item(row_index, 4, row["trend"])
        self.rank_table.resizeColumnsToContents()

    def _set_item(self, row: int, column: int, text: str) -> None:
        """设置表格单元格。"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.rank_table.setItem(row, column, item)

    def _rank_name(self, index: int, row: dict) -> str:
        """生成带排名的供应商名称。"""
        return f"{index + 1}. {row['supplier_name']}"

    def _score_bar(self, score: int) -> QProgressBar:
        """生成评分进度条。"""
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(True)
        bar.setFormat(f"{score}")
        color = "#4f7d5a" if score >= 92 else "#b56b2a"
        bar.setStyleSheet(
            "QProgressBar {"
            "background: #eee7dc;"
            "border: 1px solid #d7d2c8;"
            "border-radius: 4px;"
            "height: 10px;"
            "text-align: center;"
            "color: #252525;"
            "}"
            "QProgressBar::chunk {"
            f"background: {color};"
            "border-radius: 3px;"
            "}"
        )
        bar.animation = QPropertyAnimation(bar, b"value", bar)
        bar.animation.setStartValue(0)
        bar.animation.setEndValue(score)
        bar.animation.setDuration(760)
        bar.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        bar.animation.start()
        return bar

    def export_to_excel(self):
        """一键导出当前排名表格数据为 Excel"""
        from utils.excel_exporter import export_table_view_to_excel

        export_table_view_to_excel(self.rank_table, "供应商排名报表", self)
