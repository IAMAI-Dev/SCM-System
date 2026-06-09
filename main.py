"""供应链管理系统新版入口。"""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from ui.login_dialog import LoginDialog


def main() -> int:
    """启动 PySide6 应用。"""
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
        return 0

    session = login_dialog.user_session
    if session is not None:
        QMessageBox.information(
            None,
            "登录成功",
            f"欢迎 {session.display_name}，后续提交将进入主控制台。",
        )
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
