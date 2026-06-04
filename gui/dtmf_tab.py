import csv
import os

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import radijator


class DtmfTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.csv_edit = QLineEdit()
        self.csv_edit.setReadOnly(True)
        self.csv_edit.setPlaceholderText("No file selected")
        open_btn = QPushButton("Open existing...")
        new_btn = QPushButton("New...")
        open_btn.clicked.connect(self._open_existing)
        new_btn.clicked.connect(self._create_new)
        csv_row = QHBoxLayout()
        csv_row.addWidget(self.csv_edit, 1)
        csv_row.addWidget(open_btn)
        csv_row.addWidget(new_btn)
        csv_box = QGroupBox("CSV log file")
        cb = QVBoxLayout(csv_box)
        cb.addLayout(csv_row)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Code", "Nickname"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        table_box = QGroupBox("Existing entries")
        tb = QVBoxLayout(table_box)
        tb.addWidget(self.table)

        layout = QVBoxLayout(self)
        layout.addWidget(csv_box)
        layout.addWidget(table_box, 1)

    def _open_existing(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open DTMF CSV", "", "CSV (*.csv)")
        if path:
            self._load(path)

    def _create_new(self):
        path, _ = QFileDialog.getSaveFileName(self, "New DTMF CSV", "", "CSV (*.csv)")
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            open(path, "a", encoding="utf-8").close()
        except OSError as e:
            QMessageBox.warning(self, "Cannot create file", str(e))
            return
        self._load(path)

    def _load(self, path: str):
        self.csv_edit.setText(path)
        self.refresh_table()

    def refresh_table(self):
        path = self.csv_edit.text()
        self.table.setRowCount(0)
        if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
            return
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
        except OSError as e:
            QMessageBox.warning(self, "Cannot read CSV", str(e))
            return
        if rows and rows[0] == ["code", "nickname"]:
            rows = rows[1:]
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            code = row[0] if len(row) > 0 else ""
            nick = row[1] if len(row) > 1 else ""
            self.table.setItem(r, 0, QTableWidgetItem(code))
            self.table.setItem(r, 1, QTableWidgetItem(nick))

    def csv_path(self) -> str:
        return self.csv_edit.text().strip()

    def last_code(self) -> str | None:
        rows = self.table.rowCount()
        if rows == 0:
            return None
        item = self.table.item(rows - 1, 0)
        if item and radijator.DTMF_CODE_RE.match(item.text()):
            return item.text()
        return None

    def set_running(self, running: bool):
        self.csv_edit.setEnabled(not running)
