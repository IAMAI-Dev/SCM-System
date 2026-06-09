"""供应链管理系统新版入口。"""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox


def main() -> int:
    """启动 PySide6 应用。"""
    app = QApplication(sys.argv)
    QMessageBox.information(
        None,
        "供应链管理系统",
        "项目骨架已初始化，后续提交将接入登录和主界面。",
    )
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
