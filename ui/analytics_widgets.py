
from __future__ import annotations

"""分析页面通用图表与动效组件。"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MPL_CONFIG_DIR = PROJECT_ROOT / ".matplotlib"
MPL_CONFIG_DIR.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

from matplotlib import font_manager, rcParams
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

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
    """matplotlib 图表画布，支持悬停提示和数据防御。"""

    def __init__(self, fig: Figure | None = None, height: float = 2.2) -> None:
        """
        初始化图表画布。

        参数：
            fig: 可选的 Figure 对象。如果提供，则使用它；否则创建一个新的。
            height: 如果 fig 为 None，则使用此高度创建新 Figure。
        """
        if fig is not None:
            # 如果用户传入了 Figure 对象，直接使用它
            self.figure = fig
        else:
            # 否则，创建一个默认大小的 Figure
            self.figure = Figure(figsize=(5, height), dpi=85)

        self.figure.patch.set_facecolor(CHART_BG)
        super().__init__(self.figure)
        figure_height = float(self.figure.get_size_inches()[1])
        min_height = max(190, int(figure_height * 95))
        self.setMinimumHeight(min_height)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.setStyleSheet("background: transparent;")
        self._annotation = None
        self._hover_targets = []
        self._point_targets = []
        self.mpl_connect("motion_notify_event", self._handle_motion)

    def wheelEvent(self, event) -> None:
        """将滚轮事件透传给父级 QScrollArea，避免画布拦截滚动。"""
        scroll_area = self._find_parent_scroll_area()
        if scroll_area is not None:
            QApplication.sendEvent(scroll_area.viewport(), event)
        else:
            super().wheelEvent(event)

    def _find_parent_scroll_area(self):
        """向上查找最近的 QScrollArea。"""
        from PySide6.QtWidgets import QScrollArea
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                return parent
            parent = parent.parent()
        return None

    def _draw_empty(self, message: str) -> None:
        """绘制空状态（防御性编程：数据为空时优雅展示）。"""
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

    def _prepare_data(self, rows: list[dict], key_map: dict) -> dict:
        """
        通用数据预处理：将列表转换为字典，并过滤掉值为 0 的项。
        确保绘图函数永远不会接收到非法数据。
        """
        if not rows:
            return {}

        # 尝试从列表中的字典提取数据
        data = {}
        for row in rows:
            # 根据 key_map 提取键和值
            key = row.get(key_map.get('key', 'name')) or '未知'
            val = row.get(key_map.get('value', 'count')) or 0
            data[key] = val

        # 过滤掉值为 0 的项
        return {k: v for k, v in data.items() if v > 0}

    def draw_bar(self, rows: list[dict]) -> None:
        """绘制供应商供应量柱状图（带数据防御）。"""
        # 1. 预处理数据
        prepared_data = self._prepare_data(rows, {'key': 'supplier_name', 'value': 'part_count'})

        # 2. 如果数据为空，显示空状态
        if not prepared_data:
            self._draw_empty("暂无供应商数据")
            return

        full_names = list(prepared_data.keys())
        names = [_short_name(name) for name in full_names]
        values = list(prepared_data.values())

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        bars = ax.bar(names, values, color=COPPER)
        _style_axis(ax)
        ax.tick_params(axis="x", labelrotation=12, labelsize=8)
        _apply_chinese_font(ax)
        hover_data = [
            (bar, f"{name}\n供应件数：{int(value)}")
            for bar, name, value in zip(bars, full_names, values)
        ]
        self._set_hover_targets(ax, hover_data)
        self.figure.subplots_adjust(
            left=0.08,
            right=0.98,
            top=0.90,
            bottom=0.26,
        )
        self.draw_idle()

    def draw_donut(self, rows: list[dict]) -> None:
        """绘制供应商国家分布环形图（带数据防御）。"""
        # 1. 预处理数据
        prepared_data = self._prepare_data(rows, {'key': 'nation_name', 'value': 'supplier_count'})

        # 2. 如果数据为空，显示空状态
        if not prepared_data:
            self._draw_empty("暂无国家分布")
            return

        labels = list(prepared_data.keys())
        values = list(prepared_data.values())
        colors = [COPPER, TEAL, AMBER, GREEN, "#8b6f47", RED]

        self.figure.clear()
        ax = self.figure.add_axes((0.02, 0.05, 0.50, 0.90))
        wedges, _ = ax.pie(
            values,
            labels=None,
            colors=colors[: len(values)],
            startangle=90,
            radius=0.88,
            wedgeprops={"width": 0.36, "edgecolor": CHART_BG},
        )
        ax.set_aspect("equal")
        legend = self.figure.legend(
            wedges,
            [str(label) for label in labels],
            loc="center left",
            bbox_to_anchor=(0.56, 0.5),
            frameon=False,
            fontsize=8,
            labelcolor=TEXT_COLOR,
            borderaxespad=0,
            handletextpad=0.6,
            labelspacing=0.8,
        )
        for text in legend.get_texts():
            _set_text_font(text)
        hover_data = [
            (wedge, f"{label}\n供应商数：{int(value)}")
            for wedge, label, value in zip(wedges, labels, values)
        ]
        self._set_hover_targets(ax, hover_data)
        self.draw_idle()

    def draw_line(self, rows: list[dict]) -> None:
        """绘制采购额趋势折线图（带数据防御）。"""
        # 1. 预处理数据
        prepared_data = self._prepare_data(rows, {'key': 'month', 'value': 'purchase_amount'})

        # 2. 如果数据为空，显示空状态
        if not prepared_data:
            self._draw_empty("暂无采购趋势")
            return

        # 转换数据为绘图需要的格式
        months = [_month_label(key) for key in prepared_data.keys()]
        values = [float(val) / 10000 for val in prepared_data.values()]  # 转换为万元
        x_values = list(range(len(months)))

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(x_values, values, color=TEAL, linewidth=2.2, marker="o")
        ax.scatter(x_values, values, color=TEAL, s=30, zorder=3)
        ax.fill_between(x_values, values, color=TEAL, alpha=0.12)
        ax.set_xticks(x_values, months)
        _style_axis(ax)
        _apply_chinese_font(ax)
        point_data = [
            {
                "x": x,
                "y": y,
                "text": f"{month}\n采购额：{value:.2f} 万元",
            }
            for x, y, month, value in zip(x_values, values, months, values)
        ]
        self._set_hover_targets(ax, [], point_data)
        self.figure.subplots_adjust(
            left=0.12,
            right=0.98,
            top=0.90,
            bottom=0.24,
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
        self.animation.finished.connect(self._release_opacity_effect)
        self.animation.start()

    def _release_opacity_effect(self) -> None:
        """淡入结束后释放缓存特效，保证动态子控件正常重绘。"""
        self.setGraphicsEffect(None)
        self.opacity_effect = None


class LoadingChart(QWidget):
    """在图表完成绘制前展示局部加载状态。"""

    def __init__(self, figure: Figure, parent=None) -> None:
        super().__init__(parent)
        self._figure = figure
        self._canvas: ChartCanvas | None = None
        figure_height = float(figure.get_size_inches()[1])
        self.setMinimumHeight(max(190, int(figure_height * 95)))
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        loading_page = QWidget()
        loading_layout = QVBoxLayout(loading_page)
        loading_layout.setContentsMargins(28, 28, 28, 28)
        loading_layout.addStretch(1)
        self.loading_label = QLabel("正在加载图表数据...")
        self.loading_label.setObjectName("meta_label")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loading_bar")
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setMaximumWidth(180)
        loading_layout.addWidget(self.loading_label)
        loading_layout.addWidget(
            self.loading_bar,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )
        loading_layout.addStretch(1)

        self.stack.addWidget(loading_page)
        self.set_loading()

    @property
    def canvas(self) -> ChartCanvas:
        """首次真正绘图时才创建 Matplotlib 画布。"""
        if self._canvas is None:
            self._canvas = ChartCanvas(self._figure)
            self.stack.addWidget(self._canvas)
        return self._canvas

    def set_loading(self, message: str = "正在加载图表数据...") -> None:
        self.loading_label.setText(message)
        self.loading_bar.setVisible(True)
        self.stack.setCurrentIndex(0)

    def set_error(self, message: str) -> None:
        self.loading_label.setText(message)
        self.loading_bar.setVisible(False)
        self.stack.setCurrentIndex(0)

    def show_chart(self) -> None:
        canvas = self.canvas
        self.stack.setCurrentWidget(canvas)
        self.stack.layout().activate()
        canvas.updateGeometry()
        QTimer.singleShot(0, self._draw_visible_canvas)

    def _draw_visible_canvas(self) -> None:
        """在画布可见且布局稳定后完成 Qt 与 Matplotlib 双重刷新。"""
        canvas = self._canvas
        if canvas is None or self.stack.currentWidget() is not canvas:
            return
        canvas.draw()
        canvas.repaint()
        self.stack.repaint()


def chart_card(title: str, chart: QWidget) -> FadeFrame:
    """生成标题 + 图表卡片。"""
    from PySide6.QtWidgets import QLabel

    frame = FadeFrame()
    frame.setMinimumHeight(chart.minimumHeight() + 52)
    frame.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)
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
    if len(name) <= 4:
        return name
    return name[:4] + "..."


def _month_label(value: str) -> str:
    """格式化月份标签。"""
    if not value:
        return "--"
    return value[-2:] + "月"
