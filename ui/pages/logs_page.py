from __future__ import annotations
"""审计日志页面。"""



from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from service.admin_service import AdminService
from service.auth_service import UserSession
from ui.table_model import DictTableModel
from utils.excel_exporter import export_table_view_to_excel  # 新增：导入导出工具


class LogsPage(QWidget):
    """审计日志页面。"""

    def __init__(self, user_session: UserSession, parent=None) -> None:
        super().__init__(parent)
        self.service = AdminService(user_session)
        self.model = DictTableModel(
            [
                ("log_id", "ID"),
                ("username", "用户"),
                ("module", "模块"),
                ("action", "动作"),
                ("details", "详情"),
                ("created_at", "时间"),
            ]
        )
        self._init_ui()
        self.refresh()

    def _init_ui(self) -> None:
        """初始化页面。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        toolbar = QHBoxLayout()
        toolbar.addStretch(1)
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_button)

        # === 新增：导出 Excel 按钮 ===
        export_button = QPushButton("导出 Excel")
        export_button.clicked.connect(self.export_to_excel)
        toolbar.addWidget(export_button)


        layout.addLayout(toolbar)

        # === 修复：将 table 改为 self.table，以便其他方法访问 ===
        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        """刷新审计日志。"""
        try:
            self.model.set_rows(self.service.list_logs())
        except Exception as exc:
            QMessageBox.critical(self, "查询失败", str(exc))

    # === 新增：一键导出 Excel 方法 ===
    def export_to_excel(self):
        """一键导出当前表格数据为 Excel"""
        export_table_view_to_excel(self.table, "审计日志报表", self)
