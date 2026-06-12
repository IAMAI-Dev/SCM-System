"""供应商分析页面。"""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
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
from ui.analytics_widgets import ChartCanvas, FadeFrame, chart_card


class SuppliersPage(QWidget):
    """供应商分析页面。"""

    def __init__(
        self,
        user_session: UserSession,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.service = SupplierService(user_session)
        self.kpi_labels: list[tuple[QLabel, QLabel, QLabel]] = []
        self._init_ui()
        self.refresh()

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
        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primary_button")
        refresh_button.clicked.connect(self.refresh)
        toolbar.addLayout(title_box)
        toolbar.addStretch(1)
        toolbar.addWidget(refresh_button)
        layout.addLayout(toolbar)

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(10)
        layout.addLayout(self.kpi_grid)
        self._build_kpi_cards()

        chart_grid = QGridLayout()
        chart_grid.setSpacing(14)
        self.bar_chart = ChartCanvas(height=2.3)
        self.donut_chart = ChartCanvas(height=2.3)
        self.line_chart = ChartCanvas(height=2.0)
        chart_grid.addWidget(
            chart_card("各供应商供应量对比", self.bar_chart),
            0,
            0,
            1,
            2,
        )
        chart_grid.addWidget(
            chart_card("供应商国家分布", self.donut_chart),
            0,
            2,
        )
        chart_grid.addWidget(
            chart_card("采购额趋势（万元）", self.line_chart),
            1,
            0,
        )
        chart_grid.addWidget(self._build_rank_card(), 1, 1, 1, 2)
        chart_grid.setColumnStretch(0, 2)
        chart_grid.setColumnStretch(1, 2)
        chart_grid.setColumnStretch(2, 2)
        layout.addLayout(chart_grid)

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
        self.rank_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self.rank_table, 1)
        return card

    def refresh(self) -> None:
        """刷新供应商分析数据。"""
        try:
            analysis = self.service.load_analysis()
        except Exception as exc:
            QMessageBox.critical(self, "查询失败", str(exc))
            return

        self._apply_kpis(analysis["kpis"])
        self.bar_chart.draw_bar(analysis["bar_data"])
        self.donut_chart.draw_donut(analysis["country_data"])
        self.line_chart.draw_line(analysis["trend_data"])
        self._apply_ranking(analysis["ranking"])

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
