from __future__ import annotations

from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from service.auth_service import UserSession
from service.manager_service import ManagerService
from ui.analytics_widgets import (
    CHINESE_FONT,
    LoadingChart,
    _apply_chinese_font,
    chart_card,
)
from matplotlib.figure import Figure


class ManagerAnalysisWorker(QObject):
    """在后台线程查询经营分析数据。"""

    loaded = Signal(object)
    failed = Signal(str)

    def __init__(self, user_session: UserSession) -> None:
        super().__init__()
        self.user_session = user_session

    def run(self) -> None:
        try:
            data = ManagerService(self.user_session).load_analysis()
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.loaded.emit(data)


class ManagerDashboardPage(QWidget):
    """经理经营分析页面。"""

    def __init__(self, user_session: UserSession, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self.load_state = "idle"
        self._has_data = False
        self._load_thread: QThread | None = None
        self._load_worker: ManagerAnalysisWorker | None = None
        self._init_ui()
        QTimer.singleShot(0, self.refresh)

    def _init_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("经营分析驾驶舱")
        title.setObjectName("page_title")
        self.status_label = QLabel("等待加载")
        self.status_label.setObjectName("meta_label")
        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loading_bar")
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setFixedWidth(140)
        self.loading_bar.setVisible(False)
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("primary_button")
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.status_label)
        header.addWidget(self.loading_bar)
        header.addWidget(self.refresh_button)
        root_layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root_layout.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)
        chart_layout = QVBoxLayout(content)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(14)

        self.revenue_chart = LoadingChart(
            Figure(figsize=(7.2, 3.0), dpi=85)
        )
        self.parts_chart = LoadingChart(
            Figure(figsize=(7.2, 3.35), dpi=85)
        )
        self.customer_chart = LoadingChart(
            Figure(figsize=(7.2, 3.0), dpi=85)
        )
        chart_layout.addWidget(chart_card("营收趋势", self.revenue_chart))
        chart_layout.addWidget(chart_card("畅销零件", self.parts_chart))
        chart_layout.addWidget(chart_card("客户价值", self.customer_chart))

    def refresh(self) -> None:
        if self._load_thread is not None:
            return

        self._set_loading(True)
        self._load_thread = QThread(self)
        self._load_worker = ManagerAnalysisWorker(self.user_session)
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

    def _handle_loaded(self, data: dict) -> None:
        self.status_label.setText("正在渲染图表...")
        QTimer.singleShot(
            0,
            lambda: self._render_revenue(data["monthly_revenue"]),
        )
        QTimer.singleShot(
            60,
            lambda: self._render_parts(data["top_parts"]),
        )
        QTimer.singleShot(
            120,
            lambda: self._render_customers(data["customer_value"]),
        )

    def _render_revenue(self, rows: list[dict]) -> None:
        months = []
        revenues = []
        for row in rows:
            if row["month"] is not None and row["revenue"] is not None:
                months.append(row["month"])
                revenues.append(float(row["revenue"]) / 10000)

        canvas = self.revenue_chart.canvas
        if not months:
            canvas._draw_empty("暂无有效营收数据")
        else:
            canvas.figure.clear()
            ax = canvas.figure.add_subplot(111)
            ax.plot(
                months,
                revenues,
                marker="o",
                color="#b56b2a",
                linewidth=2,
            )
            ax.set_title("月度营收趋势 (万元)")
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis="x", rotation=38)
            self._apply_font(ax)
            canvas.figure.subplots_adjust(
                left=0.08,
                right=0.98,
                top=0.88,
                bottom=0.28,
            )
            canvas.draw_idle()
        self.revenue_chart.show_chart()

    def _render_parts(self, rows: list[dict]) -> None:
        canvas = self.parts_chart.canvas
        if not rows:
            canvas._draw_empty("暂无零件数据")
            self.parts_chart.show_chart()
            return

        full_names = [str(row["part_name"]) for row in rows]
        labels = [self._short_part_name(name) for name in full_names]
        quantities = [int(row["total_qty"]) for row in rows]
        canvas.figure.clear()
        ax = canvas.figure.add_subplot(111)
        bars = ax.bar(labels, quantities, color="#2f6f73")
        ax.set_title("Top 10 畅销零件")
        ax.tick_params(axis="x", rotation=32, labelsize=8)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment("right")
        self._apply_font(ax)
        canvas._set_hover_targets(
            ax,
            [
                (bar, f"{name}\n销量：{quantity}")
                for bar, name, quantity in zip(
                    bars,
                    full_names,
                    quantities,
                )
            ],
        )
        canvas.figure.subplots_adjust(
            left=0.15,
            right=0.985,
            top=0.88,
            bottom=0.40,
        )
        canvas.draw_idle()
        self.parts_chart.show_chart()

    def _render_customers(self, rows: list[dict]) -> None:
        canvas = self.customer_chart.canvas
        balances = [float(row["balance"] or 0) for row in rows]
        counts = [int(row["order_count"] or 0) for row in rows]
        if not rows or (not any(balances) and not any(counts)):
            canvas._draw_empty("暂无有效客户价值数据")
        else:
            canvas.figure.clear()
            ax = canvas.figure.add_subplot(111)
            ax.scatter(balances, counts, c="#c9821f", alpha=0.6)
            ax.set_title("客户价值分布 (余额 vs 订单数)")
            ax.set_xlabel("账户余额")
            ax.set_ylabel("订单数")
            self._apply_font(ax)
            canvas.figure.subplots_adjust(
                left=0.10,
                right=0.98,
                top=0.88,
                bottom=0.20,
            )
            canvas.draw_idle()
        self.customer_chart.show_chart()
        self._has_data = True
        self.load_state = "loaded"
        self._set_loading(False)
        self.status_label.setText("已加载经营分析数据")

    def _handle_failed(self, message: str) -> None:
        first_load = not self._has_data
        self.load_state = "error"
        self._set_loading(False)
        self.status_label.setText("经营分析加载失败")
        if first_load:
            for chart in (
                self.revenue_chart,
                self.parts_chart,
                self.customer_chart,
            ):
                chart.set_error("图表数据加载失败")
        QMessageBox.critical(self, "查询失败", message)

    def _set_loading(self, loading: bool) -> None:
        self.refresh_button.setEnabled(not loading)
        self.loading_bar.setVisible(loading)
        if loading:
            if not self._has_data:
                for chart in (
                    self.revenue_chart,
                    self.parts_chart,
                    self.customer_chart,
                ):
                    chart.set_loading()
            self.load_state = "loading"
            self.status_label.setText("正在加载经营分析...")

    def _clear_loader(self) -> None:
        self._load_thread = None
        self._load_worker = None

    def closeEvent(self, event) -> None:
        if self._load_thread is not None and self._load_thread.isRunning():
            self._load_thread.quit()
            self._load_thread.wait(3000)
        super().closeEvent(event)

    def _apply_font(self, ax) -> None:
        _apply_chinese_font(ax)
        if CHINESE_FONT is None:
            return
        ax.title.set_fontproperties(CHINESE_FONT)
        ax.xaxis.label.set_fontproperties(CHINESE_FONT)
        ax.yaxis.label.set_fontproperties(CHINESE_FONT)

    @staticmethod
    def _short_part_name(name: str) -> str:
        if len(name) <= 8:
            return name
        return name[:8] + "..."
