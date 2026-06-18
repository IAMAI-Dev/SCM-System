from __future__ import annotations
"""用户权限页面。"""



from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from service.admin_service import AdminService
from service.auth_service import UserSession
from service.order_service import PermissionError
from ui.table_model import DictTableModel
from utils.excel_exporter import export_table_view_to_excel  # 新增：导入导出工具


class UsersPage(QWidget):
    """用户权限管理页面。"""

    def __init__(self, user_session: UserSession, parent=None) -> None:
        super().__init__(parent)
        self.service = AdminService(user_session)
        self.model = DictTableModel(
            [
                ("user_id", "ID"),
                ("username", "用户名"),
                ("display_name", "姓名"),
                ("department", "部门"),
                ("role", "角色"),
                ("can_view", "查看"),
                ("can_insert", "新增"),
                ("can_update", "修改"),
                ("can_delete", "删除"),
                ("is_active", "启用"),
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
        update_button = QPushButton("修改权限")
        update_button.setObjectName("primary_button")
        update_button.clicked.connect(self.update_permissions)

        # === 新增：导出 Excel 按钮 ===
        export_button = QPushButton("导出 Excel")
        export_button.clicked.connect(self.export_to_excel)


        toolbar.addWidget(refresh_button)
        toolbar.addWidget(update_button)
        toolbar.addWidget(export_button)  # 加入工具栏
        layout.addLayout(toolbar)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        """刷新用户列表。"""
        try:
            self.model.set_rows(self.service.list_users())
        except (PermissionError, Exception) as exc:
            QMessageBox.critical(self, "查询失败", str(exc))

    def update_permissions(self) -> None:
        """修改选中用户权限。"""
        index = self.table.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "未选择", "请先选择用户。")
            return
        row = self.model.rows[index.row()]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"修改 {row['username']} 权限")
        layout = QVBoxLayout(dialog)
        checks = {
            "can_view": QCheckBox("查看"),
            "can_insert": QCheckBox("新增"),
            "can_update": QCheckBox("修改"),
            "can_delete": QCheckBox("删除"),
        }
        for key, check in checks.items():
            check.setChecked(bool(row[key]))
            layout.addWidget(check)
        if row.get("role") == "staff":
            checks["can_update"].setChecked(False)
            checks["can_update"].setEnabled(False)
            checks["can_delete"].setChecked(False)
            checks["can_delete"].setEnabled(False)
        ok_button = QPushButton("保存")
        ok_button.setObjectName("primary_button")
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.service.update_permissions(
                int(row["user_id"]),
                {key: check.isChecked() for key, check in checks.items()},
            )
        except (PermissionError, Exception) as exc:
            QMessageBox.critical(self, "更新失败", str(exc))
            return
        self.refresh()

    # === 新增：一键导出 Excel 方法 ===
    def export_to_excel(self):
        """一键导出当前表格数据为 Excel"""
        export_table_view_to_excel(self.table, "用户权限报表", self)
