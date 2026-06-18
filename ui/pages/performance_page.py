# ui/pages/performance_page.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from service.auth_service import UserSession
from service.performance_service import PerformanceService
from ui.table_model import DictTableModel


class PerformancePage(QWidget):
    """数据库性能监控页面。"""

    def __init__(self, user_session: UserSession, parent=None) -> None:
        super().__init__(parent)
        self.user_session = user_session
        self.service = PerformanceService(user_session)

        self.table_model = DictTableModel(
            [
                ("name", "表名"),
                ("size_mb", "大小 (MB)"),
                ("row_count", "行数"),
            ]
        )
        self.index_model = DictTableModel(
            [
                ("table_name", "表名"),
                ("index_name", "索引名"),
                ("is_unique", "唯一索引"),
            ]
        )
        self._init_ui()
        self.refresh()

    def _init_ui(self) -> None:
        """初始化页面。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        # 工具栏
        toolbar = QHBoxLayout()
        title = QLabel("数据库性能监控")
        title.setObjectName("page_title")
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        hint = QLabel(
            "提示：本页面用于查看数据库表空间占用、数据规模和非主键索引清单，供 DBA 性能调优参考。"
        )
        hint.setObjectName("meta_label")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # 表大小
        layout.addWidget(QLabel("表大小与行数"))
        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setModel(self.table_model)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        # 未使用索引
        layout.addWidget(QLabel("非主键索引清单 (仅限参考)"))
        self.index_table = QTableView()
        self.index_table.setAlternatingRowColors(True)
        self.index_table.setModel(self.index_model)
        self.index_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.index_table, 1)

    def refresh(self) -> None:
        """刷新性能数据。"""
        try:
            data = self.service.load_stats()
        except Exception as exc:
            QMessageBox.critical(self, "查询失败", str(exc))
            return

        self.table_model.set_rows(data.get("tables", []))
        self.index_model.set_rows(data.get("unused_indexes", []))
