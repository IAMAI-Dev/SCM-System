"""登录对话框。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.db import DatabaseError
from service.auth_service import AuthService, UserSession


class LoginDialog(QDialog):
    """系统登录窗口。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.auth_service = AuthService()
        self.user_session: UserSession | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化登录界面。"""
        self.setWindowTitle("供应链管理系统登录")
        self.setFixedSize(420, 320)
        self.setObjectName("login_dialog")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 24, 28, 24)
        root_layout.setSpacing(18)

        title = QLabel("供应链管理系统")
        title.setObjectName("login_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("工业调度控制台")
        subtitle.setObjectName("login_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form_frame = QFrame()
        form_frame.setObjectName("login_panel")
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(22, 20, 22, 20)
        form_layout.setSpacing(14)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("例如：admin")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("默认演示密码：123456")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.returnPressed.connect(self._handle_login)

        form_layout.addRow("用户名", self.username_edit)
        form_layout.addRow("密码", self.password_edit)

        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("取消")
        self.login_button = QPushButton("登录")
        self.login_button.setObjectName("primary_button")
        self.cancel_button.clicked.connect(self.reject)
        self.login_button.clicked.connect(self._handle_login)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        form_layout.addRow(button_layout)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(form_frame)

    def _handle_login(self) -> None:
        """处理登录按钮点击。"""
        try:
            session = self.auth_service.login(
                self.username_edit.text(),
                self.password_edit.text(),
            )
        except DatabaseError as exc:
            QMessageBox.critical(self, "连接失败", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "登录失败", f"认证服务异常：{exc}")
            return

        if session is None:
            QMessageBox.warning(self, "登录失败", "用户名或密码不正确。")
            return

        self.user_session = session
        self.accept()
