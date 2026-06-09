"""供应链管理系统新版入口。"""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
from ui.styles import INDUSTRIAL_QSS


def main() -> int:
    """启动 PySide6 应用。"""
    app = QApplication(sys.argv)
    app.setStyleSheet(INDUSTRIAL_QSS)
    login_dialog = LoginDialog()
    if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
        return 0

    session = login_dialog.user_session
    if session is not None:
        main_window = MainWindow(session)
        main_window.show()
        return app.exec()

    QMessageBox.warning(None, "启动失败", "未获取到登录会话。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
