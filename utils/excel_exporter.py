# utils/excel_exporter.py
import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget, QTableView
from PySide6.QtCore import QDateTime, Qt  # 这里加了 Qt 的导入


def export_table_view_to_excel(table_view: QTableView, default_filename: str = "数据报表", parent_widget: QWidget = None):
    """
    通用Excel导出函数：将 QTableView 的数据导出为 Excel 文件。
    """
    # 1. 检查是否有数据
    model = table_view.model()
    if model is None or model.rowCount() == 0:
        QMessageBox.warning(parent_widget, "导出失败", "当前没有数据可导出。")
        return False

    # 2. 提取表头和数据
    headers = []
    for col in range(model.columnCount()):
        header = model.headerData(col, Qt.Horizontal)  # 这里用到 Qt
        headers.append(str(header) if header is not None else f"列{col + 1}")

    data = []
    for row in range(model.rowCount()):
        row_data = []
        for col in range(model.columnCount()):
            index = model.index(row, col)
            value = model.data(index)
            row_data.append(str(value) if value is not None else "")
        data.append(row_data)

    # 3. 创建 DataFrame
    df = pd.DataFrame(data, columns=headers)

    # 4. 弹出保存文件对话框
    timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
    default_filename_full = f"{default_filename}_{timestamp}.xlsx"

    filename, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "保存 Excel 文件",
        default_filename_full,
        "Excel Files (*.xlsx);;All Files (*)"
    )

    if not filename:
        return False

    # 5. 保存文件
    try:
        df.to_excel(filename, index=False)
        QMessageBox.information(parent_widget, "导出成功", f"文件已保存至：\n{filename}")
        return True
    except Exception as e:
        QMessageBox.critical(parent_widget, "导出失败", f"保存出错：\n{str(e)}")
        return False