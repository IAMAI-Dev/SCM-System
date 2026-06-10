"""分析页面通用图表与动效组件。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from matplotlib import font_manager, rcParams
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QVariantAnimation
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QVBoxLayout


CHART_BG = "#fffdf8"
TEXT_COLOR = "#3f3f3a"
GRID_COLOR = "#e8e1d6"
COPPER = "#b56b2a"
GREEN = "#4f7d5a"
TEAL = "#2f6f73"
AMBER = "#c9821f"
RED = "#b84536"
CHINESE_FONT = None


def configure_matplotlib_fonts() -> None:
    """配置 matplotlib 中文字体。"""
    global CHINESE_FONT
    if CHINESE_FONT is not None:
        return

    candidate_files = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
    ]
    for font_path in candidate_files:
        path = Path(font_path)
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            CHINESE_FONT = font_manager.FontProperties(fname=str(path))
            rcParams["font.sans-serif"] = [
                CHINESE_FONT.get_name(),
                "Microsoft YaHei",
                "SimHei",
                "Arial Unicode MS",
            ]
            rcParams["axes.unicode_minus"] = False
            return

    for font_info in font_manager.fontManager.ttflist:
        if font_info.name in {"Microsoft YaHei", "SimHei", "SimSun"}:
            CHINESE_FONT = font_manager.FontProperties(fname=font_info.fname)
            rcParams["font.sans-serif"] = [font_info.name]
            rcParams["axes.unicode_minus"] = False
            return

    rcParams["axes.unicode_minus"] = False


configure_matplotlib_fonts()


class ChartCanvas(FigureCanvasQTAgg):
    """matplotlib 图表画布，支持简单增长动画。"""

    def __init__(self, height: float = 2.2) -> None:
        self.figure = Figure(figsize=(5, height), dpi=100)
        self.figure.patch.set_facecolor(CHART_BG)
        super().__init__(self.figure)
        self.setStyleSheet("background: transparent;")
        self._draw_callback: Callable[[float], None] | None = None
        self._animation: QVariantAnimation | None = None
        self._annotation = None
        self._hover_targets = []
        self._point_targets = []
        self.mpl_connect("motion_notify_event", self._handle_motion)

    def animate(self, callback: Callable[[float], None]) -> None:
        """执行图表从 0 到 1 的增长动画。"""
        self._draw_callback = callback
        self._animation = QVariantAnimation(self)
        self._animation.setStartValue(0.05)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(920)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
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
            bars = ax.bar(
                names,
                [value * progress for value in values],
                color=COPPER,
            )
            _style_axis(ax)
            ax.tick_params(axis="x", labelrotation=0, labelsize=8)
            _apply_chinese_font(ax)
            self._set_hover_targets(
                ax,
                [
                    (bar, f"{name}\n供应件数：{value}")
                    for bar, name, value in zip(bars, names, values)
                ],
            )
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
            wedges, texts = ax.pie(
                safe_values,
                labels=labels,
                colors=colors[: len(values)],
                startangle=90,
                wedgeprops={"width": 0.36, "edgecolor": CHART_BG},
                textprops={
                    "fontsize": 8,
                    "color": TEXT_COLOR,
                    "fontproperties": CHINESE_FONT,
                },
            )
            for text in texts:
                _set_text_font(text)
            ax.set_aspect("equal")
            self._set_hover_targets(
                ax,
                [
                    (wedge, f"{label}\n供应商数：{value}")
                    for wedge, label, value in zip(wedges, labels, values)
                ],
            )
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
            ax.scatter(x_values, y_values, color=TEAL, s=30, zorder=3)
            ax.fill_between(x_values, y_values, color=TEAL, alpha=0.12)
            ax.set_xticks(x_values, months)
            _style_axis(ax)
            _apply_chinese_font(ax)
            self._set_hover_targets(
                ax,
                [],
                [
                    {
                        "x": x,
                        "y": y,
                        "text": f"{month}\n采购额：{value:.2f} 万元",
                    }
                    for x, y, month, value in zip(
                        x_values,
                        y_values,
                        months,
                        values,
                    )
                ],
            )
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
            fontproperties=CHINESE_FONT,
        )
        self.draw_idle()

    def _set_hover_targets(
        self,
        ax,
        targets: list,
        point_targets: list[dict] | None = None,
    ) -> None:
        """设置当前图表的悬停目标。"""
        self._hover_targets = targets
        self._point_targets = point_targets or []
        self._annotation = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox={
                "boxstyle": "round,pad=0.35",
                "fc": "#fffdf8",
                "ec": "#d7d2c8",
                "alpha": 0.96,
            },
            arrowprops={"arrowstyle": "->", "color": "#b56b2a"},
            fontproperties=CHINESE_FONT,
            fontsize=9,
            color=TEXT_COLOR,
        )
        self._annotation.set_visible(False)

    def _handle_motion(self, event) -> None:
        """处理鼠标悬停提示。"""
        if event.inaxes is None or self._annotation is None:
            self._hide_annotation()
            return

        for artist, text in self._hover_targets:
            contains, _ = artist.contains(event)
            if contains:
                self._show_annotation(event.xdata, event.ydata, text)
                return

        point = self._nearest_point(event)
        if point is not None:
            self._show_annotation(point["x"], point["y"], point["text"])
            return

        self._hide_annotation()

    def _nearest_point(self, event) -> dict | None:
        """查找离鼠标最近的折线点。"""
        if event.xdata is None or event.ydata is None:
            return None
        for point in self._point_targets:
            display_x, display_y = event.inaxes.transData.transform(
                (point["x"], point["y"])
            )
            distance = (
                (display_x - event.x) ** 2
                + (display_y - event.y) ** 2
            ) ** 0.5
            if distance <= 12:
                return point
        return None

    def _show_annotation(self, x_value, y_value, text: str) -> None:
        """显示悬停提示。"""
        if self._annotation is None:
            return
        self._annotation.xy = (x_value, y_value)
        self._annotation.set_text(text)
        self._annotation.set_visible(True)
        self.draw_idle()

    def _hide_annotation(self) -> None:
        """隐藏悬停提示。"""
        if self._annotation is not None and self._annotation.get_visible():
            self._annotation.set_visible(False)
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


def _apply_chinese_font(ax) -> None:
    """为坐标轴文本应用中文字体。"""
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        _set_text_font(label)


def _set_text_font(text) -> None:
    """为 matplotlib 文本对象设置中文字体。"""
    if CHINESE_FONT is not None:
        text.set_fontproperties(CHINESE_FONT)


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
