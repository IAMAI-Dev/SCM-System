"""分析页面通用图表与动效组件。"""

from __future__ import annotations

from collections.abc import Callable

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QPropertyAnimation, QVariantAnimation
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QVBoxLayout


CHART_BG = "#fffdf8"
TEXT_COLOR = "#3f3f3a"
GRID_COLOR = "#e8e1d6"
COPPER = "#b56b2a"
GREEN = "#4f7d5a"
TEAL = "#2f6f73"
AMBER = "#c9821f"
RED = "#b84536"


class ChartCanvas(FigureCanvasQTAgg):
    """matplotlib 图表画布，支持简单增长动画。"""

    def __init__(self, height: float = 2.2) -> None:
        self.figure = Figure(figsize=(5, height), dpi=100)
        self.figure.patch.set_facecolor(CHART_BG)
        super().__init__(self.figure)
        self.setStyleSheet("background: transparent;")
        self._draw_callback: Callable[[float], None] | None = None
        self._animation: QVariantAnimation | None = None

    def animate(self, callback: Callable[[float], None]) -> None:
        """执行图表从 0 到 1 的增长动画。"""
        self._draw_callback = callback
        self._animation = QVariantAnimation(self)
        self._animation.setStartValue(0.05)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(620)
        self._animation.valueChanged.connect(self._render_progress)
        self._animation.start()

    def _render_progress(self, value) -> None:
        """按进度重绘图表。"""
        if self._draw_callback is not None:
            self._draw_callback(float(value))

    def draw_bar(self, rows: list[dict]) -> None:
        """绘制供应商供应量柱状图。"""
        if not rows:
            self._draw_empty("暂无供应商数据")
            return

        names = [_short_name(row["supplier_name"]) for row in rows]
        values = [int(row["part_count"] or 0) for row in rows]

        def render(progress: float) -> None:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.bar(names, [value * progress for value in values], color=COPPER)
            _style_axis(ax)
            ax.tick_params(axis="x", labelrotation=0, labelsize=8)
            self.figure.tight_layout(pad=1.0)
            self.draw_idle()

        self.animate(render)

    def draw_donut(self, rows: list[dict]) -> None:
        """绘制供应商国家分布环形图。"""
        if not rows:
            self._draw_empty("暂无国家分布")
            return

        labels = [row["nation_name"] for row in rows]
        values = [int(row["supplier_count"] or 0) for row in rows]
        colors = [COPPER, TEAL, AMBER, GREEN, "#8b6f47", RED]

        def render(progress: float) -> None:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            safe_values = [max(value * progress, 0.01) for value in values]
            ax.pie(
                safe_values,
                labels=labels,
                colors=colors[: len(values)],
                startangle=90,
                wedgeprops={"width": 0.36, "edgecolor": CHART_BG},
                textprops={"fontsize": 8, "color": TEXT_COLOR},
            )
            ax.set_aspect("equal")
            self.figure.tight_layout(pad=0.8)
            self.draw_idle()

        self.animate(render)

    def draw_line(self, rows: list[dict]) -> None:
        """绘制采购额趋势折线图。"""
        if not rows:
            self._draw_empty("暂无采购趋势")
            return

        months = [_month_label(row["month"]) for row in rows]
        values = [float(row["purchase_amount"] or 0) / 10000 for row in rows]
        x_values = list(range(len(months)))

        def render(progress: float) -> None:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            y_values = [value * progress for value in values]
            ax.plot(x_values, y_values, color=TEAL, linewidth=2.2, marker="o")
            ax.fill_between(x_values, y_values, color=TEAL, alpha=0.12)
            ax.set_xticks(x_values, months)
            _style_axis(ax)
            self.figure.tight_layout(pad=1.0)
            self.draw_idle()

        self.animate(render)

    def _draw_empty(self, message: str) -> None:
        """绘制空状态。"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_axis_off()
        ax.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            color="#8a867d",
            fontsize=10,
        )
        self.draw_idle()


class FadeFrame(QFrame):
    """带淡入效果的内容卡片。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("analytics_card")
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)
        self.animation = QPropertyAnimation(
            self.opacity_effect,
            b"opacity",
            self,
        )
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setDuration(420)
        self.animation.start()


def chart_card(title: str, chart: ChartCanvas) -> FadeFrame:
    """生成标题 + 图表卡片。"""
    from PySide6.QtWidgets import QLabel

    frame = FadeFrame()
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    label = QLabel(title)
    label.setObjectName("section_title")
    layout.addWidget(label)
    layout.addWidget(chart, 1)
    return frame


def _style_axis(ax) -> None:
    """统一图表坐标轴样式。"""
    ax.set_facecolor(CHART_BG)
    ax.grid(axis="y", color=GRID_COLOR, linestyle="--", linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.tick_params(colors="#8a867d", labelsize=8)


def _short_name(name: str) -> str:
    """生成较短的供应商名称标签。"""
    if len(name) <= 6:
        return name
    return name[:6]


def _month_label(value: str) -> str:
    """格式化月份标签。"""
    if not value:
        return "--"
    return value[-2:] + "月"
