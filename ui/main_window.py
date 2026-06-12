"""主窗口与工业控制台布局。"""

from __future__ import annotations

import sys
from collections.abc import Callable
from ctypes import wintypes

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.config import load_app_config
from service.auth_service import UserSession


class MainWindow(QMainWindow):
    """供应链管理系统主窗口。"""

    RESIZE_MARGIN = 10

    def __init__(self, user_session: UserSession) -> None:
        super().__init__()
        self.user_session = user_session
        self.app_config = load_app_config()
        self.page_titles: dict[str, str] = {}
        self.nav_buttons: dict[str, QPushButton] = {}
        self.page_factories: dict[str, Callable[[], QWidget]] = {}
        self.page_containers: dict[str, QWidget] = {}
        self.loaded_pages: set[str] = set()
        self.current_page_key = ""
        self._resize_cursor_widget: QWidget | None = None
        self._init_ui()
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        self._switch_page("dashboard")

    def _init_ui(self) -> None:
        """初始化主窗口布局。"""
        self.setWindowTitle("供应链管理系统")
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(1320, 840)
        self.setMinimumSize(980, 620)

        central = QWidget()
        central.setObjectName("app_root")
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_workspace(), 1)

        self.setCentralWidget(central)
        self._enable_resize_tracking(central)

    def _build_sidebar(self) -> QFrame:
        """构建左侧导航栏。"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 20, 0, 18)
        layout.setSpacing(8)

        brand = QLabel("SCM Console")
        brand.setObjectName("brand_title")
        subtitle = QLabel("供应链调度平台")
        subtitle.setObjectName("brand_subtitle")
        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        caption = QLabel("功能导航")
        caption.setObjectName("sidebar_caption")
        layout.addWidget(caption)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        nav_items = [
            ("dashboard", "总览仪表盘"),
            ("orders", "订单管理"),
            ("inventory", "库存调度"),
            ("customers", "客户管理"),
            ("suppliers", "供应商分析"),
            ("users", "用户权限"),
            ("logs", "审计日志"),
        ]
        for page_key, title in nav_items:
            if not self.user_session.can_access_module(page_key):
                continue
            button = QPushButton(title)
            button.setObjectName("nav_button")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, key=page_key: self._switch_page(key)
            )
            self.button_group.addButton(button)
            self.nav_buttons[page_key] = button
            layout.addWidget(button)

        layout.addStretch(1)
        user_label = QLabel(
            f"{self.user_session.display_name}\n"
            f"{self.user_session.department_label} / {self.user_session.role}"
        )
        user_label.setObjectName("sidebar_caption")
        layout.addWidget(user_label)
        return sidebar

    def _build_workspace(self) -> QWidget:
        """构建右侧工作区。"""
        workspace = QWidget()
        workspace.setObjectName("workspace")
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.page_title = QLabel()
        self.page_title.setObjectName("page_title")
        top_bar = self._build_top_bar()
        top_bar.mousePressEvent = self._start_window_move
        top_bar.mouseDoubleClickEvent = self._toggle_maximized_from_event
        layout.addWidget(top_bar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("page_stack")
        self.stack.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(self.stack, 1)

        self._register_page(
            "dashboard",
            "总览仪表盘",
            self._create_dashboard_page,
        )
        if self.user_session.can_access_module("orders"):
            self._register_page("orders", "订单管理", self._create_orders_page)
        if self.user_session.can_access_module("inventory"):
            self._register_page(
                "inventory",
                "库存调度",
                self._create_inventory_page,
            )
        if self.user_session.can_access_module("customers"):
            self._register_page(
                "customers",
                "客户管理",
                self._create_customers_page,
            )
        if self.user_session.can_access_module("suppliers"):
            self._register_page(
                "suppliers",
                "供应商分析",
                self._create_suppliers_page,
            )
        if self.user_session.can_access_module("users"):
            self._register_page("users", "用户权限", self._create_users_page)
        if self.user_session.can_access_module("logs"):
            self._register_page("logs", "审计日志", self._create_logs_page)
        return workspace

    def _register_page(
        self,
        page_key: str,
        title: str,
        factory: Callable[[], QWidget],
    ) -> None:
        """注册业务页面，进入时再懒加载真实内容。"""
        self.page_titles[page_key] = title
        self.page_factories[page_key] = factory
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(18, 18, 18, 18)

        placeholder = QFrame()
        placeholder.setObjectName("content_panel")
        placeholder.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.setContentsMargins(22, 20, 22, 20)
        label = QLabel("正在准备页面数据...")
        label.setObjectName("meta_label")
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        placeholder_layout.addWidget(label)
        placeholder_layout.addStretch(1)
        container_layout.addWidget(placeholder, 1)

        self.page_containers[page_key] = container
        self.stack.addWidget(container)

    def _build_top_bar(self) -> QFrame:
        """构建顶部工具栏。"""
        top_bar = QFrame()
        top_bar.setObjectName("top_bar")
        top_bar.setFixedHeight(74)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(22, 0, 22, 0)
        layout.setSpacing(14)

        layout.addWidget(self.page_title)
        self.page_title.mousePressEvent = self._start_window_move

        search = QLineEdit()
        search.setPlaceholderText("全局搜索订单、客户、零件或供应商")
        search.setFixedWidth(360)
        layout.addWidget(search)
        layout.addStretch(1)

        meta = QLabel(
            f"仓库：{self.app_config.warehouse}    "
            f"账套：{self.app_config.account_set}    "
            "同步：本地"
        )
        meta.setObjectName("meta_label")
        meta.mousePressEvent = self._start_window_move
        layout.addWidget(meta)
        layout.addLayout(self._build_window_buttons())
        return top_bar

    def _build_window_buttons(self) -> QHBoxLayout:
        """构建嵌入式窗口控制按钮。"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        button_layout.setContentsMargins(8, 0, 0, 0)

        minimize_button = self._window_button("-", "最小化")
        minimize_button.clicked.connect(self.showMinimized)
        self.maximize_button = self._window_button("□", "最大化")
        self.maximize_button.clicked.connect(self._toggle_maximized)
        close_button = self._window_button("×", "关闭")
        close_button.setObjectName("window_close_button")
        close_button.clicked.connect(self.close)

        button_layout.addWidget(minimize_button)
        button_layout.addWidget(self.maximize_button)
        button_layout.addWidget(close_button)
        return button_layout

    def _window_button(self, text: str, tooltip: str) -> QPushButton:
        """创建窗口控制按钮。"""
        button = QPushButton(text)
        button.setObjectName("window_button")
        button.setToolTip(tooltip)
        button.setFixedSize(38, 30)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def _start_window_move(self, event) -> None:
        """从自定义顶部栏拖动窗口。"""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._resize_edges_at(self._event_global_pos(event)):
            return
        handle = self.windowHandle()
        if handle is not None:
            handle.startSystemMove()
            event.accept()

    def _toggle_maximized_from_event(self, event) -> None:
        """双击自定义顶部栏切换最大化。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximized()
            event.accept()

    def _toggle_maximized(self) -> None:
        """切换窗口最大化状态。"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._sync_window_buttons()

    def _sync_window_buttons(self) -> None:
        """同步窗口按钮展示。"""
        if hasattr(self, "maximize_button"):
            self.maximize_button.setText("▢" if self.isMaximized() else "□")

    def eventFilter(self, watched, event) -> bool:
        """在所有子控件边缘提供无边框窗口缩放。"""
        if isinstance(watched, QWidget) and watched.window() is self:
            if event.type() == QEvent.Type.MouseMove:
                self._update_resize_cursor(watched, event)
            elif event.type() == QEvent.Type.MouseButtonPress:
                if self._start_window_resize(event):
                    return True
            elif event.type() == QEvent.Type.Leave:
                if watched is self._resize_cursor_widget:
                    self._clear_resize_cursor()
        return super().eventFilter(watched, event)

    def changeEvent(self, event) -> None:
        """同步窗口状态变化。"""
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._sync_window_buttons()

    def nativeEvent(self, event_type, message):
        """让无边框窗口在 Windows 下保留原生边缘缩放。"""
        if sys.platform != "win32" or self.isMaximized():
            return super().nativeEvent(event_type, message)

        msg = wintypes.MSG.from_address(int(message))
        if msg.message != 0x0084:  # WM_NCHITTEST
            return super().nativeEvent(event_type, message)

        global_pos = QPoint(
            _signed_low_word(msg.lParam),
            _signed_high_word(msg.lParam),
        )
        local_pos = self.mapFromGlobal(global_pos)
        if not self.rect().contains(local_pos):
            return super().nativeEvent(event_type, message)

        margin = self.RESIZE_MARGIN
        left = local_pos.x() <= margin
        right = local_pos.x() >= self.width() - margin
        top = local_pos.y() <= margin
        bottom = local_pos.y() >= self.height() - margin

        if top and left:
            return True, 13  # HTTOPLEFT
        if top and right:
            return True, 14  # HTTOPRIGHT
        if bottom and left:
            return True, 16  # HTBOTTOMLEFT
        if bottom and right:
            return True, 17  # HTBOTTOMRIGHT
        if left:
            return True, 10  # HTLEFT
        if right:
            return True, 11  # HTRIGHT
        if top:
            return True, 12  # HTTOP
        if bottom:
            return True, 15  # HTBOTTOM
        return super().nativeEvent(event_type, message)

    def _enable_resize_tracking(self, widget: QWidget) -> None:
        """让边缘上的子控件也能产生鼠标移动事件。"""
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)

    def _start_window_resize(self, event) -> bool:
        """从窗口边缘启动系统缩放。"""
        if event.button() != Qt.MouseButton.LeftButton:
            return False

        edges = self._resize_edges_at(self._event_global_pos(event))
        if not edges:
            return False

        handle = self.windowHandle()
        if handle is None:
            return False

        started = handle.startSystemResize(edges)
        if started:
            event.accept()
        return started

    def _update_resize_cursor(self, watched: QWidget, event) -> None:
        """鼠标靠近窗口边缘时显示缩放光标。"""
        cursor_shape = self._resize_cursor_for_edges(
            self._resize_edges_at(self._event_global_pos(event))
        )
        if cursor_shape is None:
            self._clear_resize_cursor()
            return

        if self._resize_cursor_widget is not watched:
            self._clear_resize_cursor()
            self._resize_cursor_widget = watched
        watched.setCursor(cursor_shape)

    def _clear_resize_cursor(self) -> None:
        """清除边缘缩放光标。"""
        if self._resize_cursor_widget is not None:
            self._resize_cursor_widget.unsetCursor()
            self._resize_cursor_widget = None

    def _resize_edges_at(self, global_pos: QPoint | None):
        """返回指定全局坐标命中的窗口缩放边缘。"""
        if global_pos is None or self.isMaximized() or self.isFullScreen():
            return Qt.Edges()

        local_pos = self.mapFromGlobal(global_pos)
        if not self.rect().contains(local_pos):
            return Qt.Edges()

        margin = self.RESIZE_MARGIN
        edges = Qt.Edges()
        if local_pos.x() <= margin:
            edges |= Qt.Edge.LeftEdge
        elif local_pos.x() >= self.width() - margin:
            edges |= Qt.Edge.RightEdge

        if local_pos.y() <= margin:
            edges |= Qt.Edge.TopEdge
        elif local_pos.y() >= self.height() - margin:
            edges |= Qt.Edge.BottomEdge
        return edges

    def _resize_cursor_for_edges(self, edges):
        """根据缩放边缘返回鼠标光标。"""
        if not edges:
            return None

        left = bool(edges & Qt.Edge.LeftEdge)
        right = bool(edges & Qt.Edge.RightEdge)
        top = bool(edges & Qt.Edge.TopEdge)
        bottom = bool(edges & Qt.Edge.BottomEdge)

        if (top and left) or (bottom and right):
            return Qt.CursorShape.SizeFDiagCursor
        if (top and right) or (bottom and left):
            return Qt.CursorShape.SizeBDiagCursor
        if left or right:
            return Qt.CursorShape.SizeHorCursor
        if top or bottom:
            return Qt.CursorShape.SizeVerCursor
        return None

    def _event_global_pos(self, event) -> QPoint | None:
        """兼容 Qt6 鼠标事件全局坐标。"""
        if hasattr(event, "globalPosition"):
            return event.globalPosition().toPoint()
        if hasattr(event, "globalPos"):
            return event.globalPos()
        return None

    def _switch_page(self, page_key: str) -> None:
        """切换当前页面。"""
        index = list(self.page_titles.keys()).index(page_key)
        self.stack.setCurrentIndex(index)
        self.page_title.setText(self.page_titles[page_key])
        self.current_page_key = page_key
        button = self.nav_buttons.get(page_key)
        if button is not None:
            button.setChecked(True)
        if page_key not in self.loaded_pages:
            QTimer.singleShot(
                0,
                lambda key=page_key: self._ensure_page_loaded(key),
            )

    def _ensure_page_loaded(self, page_key: str) -> None:
        """按需创建页面内容。"""
        if page_key in self.loaded_pages:
            return

        container = self.page_containers[page_key]
        layout = container.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        page = self.page_factories[page_key]()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(page)
        self._enable_resize_tracking(page)
        self.loaded_pages.add(page_key)

    def _create_dashboard_page(self) -> QWidget:
        """创建总览页面。"""
        from ui.pages.dashboard_page import DashboardPage

        return DashboardPage()

    def _create_orders_page(self) -> QWidget:
        """创建订单页面。"""
        from ui.pages.orders_page import OrdersPage

        return OrdersPage(self.user_session)

    def _create_inventory_page(self) -> QWidget:
        """创建库存页面。"""
        from ui.pages.inventory_page import InventoryPage

        return InventoryPage(self.user_session)

    def _create_customers_page(self) -> QWidget:
        """创建客户页面。"""
        from ui.pages.customers_page import CustomersPage

        return CustomersPage(self.user_session)

    def _create_suppliers_page(self) -> QWidget:
        """创建供应商页面。"""
        from ui.pages.suppliers_page import SuppliersPage

        return SuppliersPage(self.user_session)

    def _create_users_page(self) -> QWidget:
        """创建用户页面。"""
        from ui.pages.users_page import UsersPage

        return UsersPage(self.user_session)

    def _create_logs_page(self) -> QWidget:
        """创建日志页面。"""
        from ui.pages.logs_page import LogsPage

        return LogsPage(self.user_session)


def _signed_low_word(value: int) -> int:
    """读取 Windows lParam 低位有符号坐标。"""
    result = value & 0xFFFF
    return result - 0x10000 if result & 0x8000 else result


def _signed_high_word(value: int) -> int:
    """读取 Windows lParam 高位有符号坐标。"""
    result = (value >> 16) & 0xFFFF
    return result - 0x10000 if result & 0x8000 else result
