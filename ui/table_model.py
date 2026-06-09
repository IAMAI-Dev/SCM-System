"""通用表格数据模型。"""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class DictTableModel(QAbstractTableModel):
    """基于字典列表的通用表格模型。"""

    def __init__(
        self,
        headers: list[tuple[str, str]],
        rows: list[dict] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.headers = headers
        self.rows = rows or []

    def rowCount(self, parent=QModelIndex()) -> int:
        """返回行数。"""
        if parent.isValid():
            return 0
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        """返回列数。"""
        if parent.isValid():
            return 0
        return len(self.headers)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        """返回单元格展示数据。"""
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        key = self.headers[index.column()][0]
        value = self.rows[index.row()].get(key, "")
        return "" if value is None else str(value)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role=Qt.ItemDataRole.DisplayRole,
    ):
        """返回表头数据。"""
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.headers[section][1]
        return str(section + 1)

    def set_rows(self, rows: list[dict]) -> None:
        """替换表格数据。"""
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()
