"""供应链管理系统 QSS 样式。"""

INDUSTRIAL_QSS = """
QWidget {
    background-color: #f3f1ec;
    color: #3f3f3a;
    font-family: "Microsoft YaHei", "Segoe UI", Arial;
    font-size: 10pt;
}

QMainWindow {
    background-color: #f3f1ec;
}

QWidget#app_root {
    background-color: #f3f1ec;
    border: 1px solid #bdb7ad;
}

QFrame#sidebar {
    background-color: #1f2428;
    border: none;
}

QLabel#brand_title {
    background-color: transparent;
    color: #fffdf8;
    font-size: 15pt;
    font-weight: 700;
}

QLabel#brand_subtitle,
QLabel#sidebar_caption {
    background-color: transparent;
    color: #b8b7b0;
}

QPushButton#nav_button {
    background-color: transparent;
    color: #d7d2c8;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    padding: 10px 14px;
    text-align: left;
}

QPushButton#nav_button:hover {
    background-color: #2b3035;
    color: #fffdf8;
}

QPushButton#nav_button:checked {
    background-color: #30343a;
    border-left: 3px solid #b56b2a;
    color: #fffdf8;
    font-weight: 600;
}

QFrame#top_bar {
    background-color: #f8f5ee;
    border-bottom: 1px solid #d7d2c8;
}

QLabel#page_title {
    background-color: transparent;
    color: #252525;
    font-size: 16pt;
    font-weight: 700;
}

QLabel#meta_label {
    background-color: transparent;
    color: #6b6a66;
}

QLineEdit {
    background-color: #fffdf8;
    border: 1px solid #d7d2c8;
    border-radius: 4px;
    padding: 7px 10px;
    selection-background-color: #e7c18d;
}

QLineEdit:focus {
    border: 1px solid #b56b2a;
}

QPushButton {
    background-color: #fffdf8;
    border: 1px solid #d7d2c8;
    border-radius: 4px;
    color: #3f3f3a;
    padding: 7px 12px;
}

QPushButton:hover {
    background-color: #f4eadc;
    border-color: #b56b2a;
}

QPushButton#primary_button {
    background-color: #b56b2a;
    border: 1px solid #b56b2a;
    color: #fffdf8;
    font-weight: 600;
}

QPushButton#primary_button:hover {
    background-color: #9d5c25;
}

QPushButton#window_button,
QPushButton#window_close_button {
    background-color: transparent;
    border: none;
    border-radius: 3px;
    color: #5f5d58;
    font-size: 11pt;
    font-weight: 600;
    padding: 0;
}

QPushButton#window_button:hover {
    background-color: #e7dfd1;
    color: #252525;
}

QPushButton#window_close_button:hover {
    background-color: #b84536;
    color: #fffdf8;
}

QFrame#content_panel,
QFrame#login_panel,
QFrame#analytics_card {
    background-color: #fffdf8;
    border: 1px solid #d7d2c8;
    border-radius: 6px;
}

QLabel#section_title {
    background-color: transparent;
    color: #252525;
    font-size: 11pt;
    font-weight: 700;
}

QLabel#kpi_value {
    background-color: transparent;
    color: #252525;
    font-size: 20pt;
    font-weight: 700;
}

QLabel#login_title {
    background-color: transparent;
    color: #252525;
    font-size: 20pt;
    font-weight: 700;
}

QLabel#login_subtitle {
    background-color: transparent;
    color: #6b6a66;
}

QHeaderView::section {
    background-color: #ebe6dc;
    color: #252525;
    border: none;
    border-right: 1px solid #d7d2c8;
    border-bottom: 1px solid #d7d2c8;
    padding: 7px;
    font-weight: 600;
}

QTableView {
    background-color: #fffdf8;
    alternate-background-color: #fbf7ef;
    border: 1px solid #d7d2c8;
    gridline-color: #e6dfd2;
    selection-background-color: #f0d8ae;
    selection-color: #252525;
}

QTableView::item {
    padding: 5px;
}

QTableWidget {
    background-color: #fffdf8;
    alternate-background-color: #fbf7ef;
    border: 1px solid #d7d2c8;
    gridline-color: #e6dfd2;
    selection-background-color: #f0d8ae;
    selection-color: #252525;
}

QTableWidget::item {
    padding: 5px;
}

QScrollArea {
    border: none;
    background-color: #f3f1ec;
}
"""
