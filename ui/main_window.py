"""主窗口与工业控制台布局。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
from ui.pages.dashboard_page import DashboardPage
from ui.pages.inventory_page import InventoryPage
from ui.pages.orders_page import OrdersPage


class MainWindow(QMainWindow):
    """供应链管理系统主窗口。"""

    def __init__(self, user_session: UserSession) -> None:
        super().__init__()
        self.user_session = user_session
        self.app_config = load_app_config()
        self.page_titles: dict[str, str] = {}
        self.nav_buttons: dict[str, QPushButton] = {}
        self._init_ui()
        self._switch_page("dashboard")

    def _init_ui(self) -> None:
        """初始化主窗口布局。"""
        self.setWindowTitle("供应链管理系统")
        self.resize(1320, 840)

        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_workspace(), 1)

        self.setCentralWidget(central)

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
            if page_key == "users" and not self.user_session.is_manager:
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
            f"{self.user_session.department} / {self.user_session.role}"
        )
        user_label.setObjectName("sidebar_caption")
        layout.addWidget(user_label)
        return sidebar

    def _build_workspace(self) -> QWidget:
        """构建右侧工作区。"""
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.page_title = QLabel()
        self.page_title.setObjectName("page_title")
        top_bar = self._build_top_bar()
        layout.addWidget(top_bar)

        self.stack = QStackedWidget()
        self.stack.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(self.stack, 1)

        self._add_page("dashboard", "总览仪表盘", DashboardPage())
        self._add_page("orders", "订单管理", OrdersPage(self.user_session))
        self._add_page(
            "inventory",
            "库存调度",
            InventoryPage(self.user_session),
        )
        self._add_placeholder_page("customers", "客户管理")
        self._add_placeholder_page("suppliers", "供应商分析")
        self._add_placeholder_page("users", "用户权限")
        self._add_placeholder_page("logs", "审计日志")
        return workspace

    def _add_page(
        self,
        page_key: str,
        title: str,
        widget: QWidget,
    ) -> None:
        """添加业务页面。"""
        self.page_titles[page_key] = title
        self.stack.addWidget(widget)

    def _build_top_bar(self) -> QFrame:
        """构建顶部工具栏。"""
        top_bar = QFrame()
        top_bar.setObjectName("top_bar")
        top_bar.setFixedHeight(74)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(22, 0, 22, 0)
        layout.setSpacing(14)

        layout.addWidget(self.page_title)

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
        layout.addWidget(meta)
        return top_bar

    def _add_placeholder_page(self, page_key: str, title: str) -> None:
        """添加占位页面。"""
        panel = QFrame()
        panel.setObjectName("content_panel")
        panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        label = QLabel(f"{title}模块将在后续阶段接入业务数据。")
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        label.setObjectName("meta_label")
        layout.addWidget(label)
        layout.addStretch(1)

        self.page_titles[page_key] = title
        self.stack.addWidget(panel)

    def _switch_page(self, page_key: str) -> None:
        """切换当前页面。"""
        index = list(self.page_titles.keys()).index(page_key)
        self.stack.setCurrentIndex(index)
        self.page_title.setText(self.page_titles[page_key])
        button = self.nav_buttons.get(page_key)
        if button is not None:
            button.setChecked(True)
