"""供应链管理系统新版入口。"""

import sys
import threading

from PySide6.QtWidgets import QApplication, QMessageBox

from core.db import DatabaseError, initialize_database_objects
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
from ui.styles import INDUSTRIAL_QSS


def _preload_analytics() -> None:
    """在登录界面显示期间预热 Matplotlib 与中文字体缓存。"""
    try:
        from ui import analytics_widgets  # noqa: F401
    except Exception:
        return


def main() -> int:
    """启动 PySide6 应用。"""
    app = QApplication(sys.argv)
    app.setStyleSheet(INDUSTRIAL_QSS)
    threading.Thread(target=_preload_analytics, daemon=True).start()
    try:
        initialize_database_objects()
    except DatabaseError as exc:
        QMessageBox.warning(None, "数据库初始化失败", str(exc))
    except Exception as exc:
        QMessageBox.warning(None, "数据库初始化失败", f"初始化异常：{exc}")

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
