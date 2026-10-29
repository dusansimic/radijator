from PySide6.QtCore import QRegularExpression, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
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
    csv_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []
        self._error = None
        self._running = False

        self.csv_edit = QLineEdit()
        self.csv_edit.setReadOnly(True)
        self.csv_edit.setPlaceholderText("No file selected")
        self.open_btn = QPushButton("Open existing...")
        self.new_btn = QPushButton("New...")
        self.reload_btn = QPushButton("Reload")
        self.open_btn.clicked.connect(self._open_existing)
        self.new_btn.clicked.connect(self._create_new)
        self.reload_btn.clicked.connect(self.refresh_table)
        csv_row = QHBoxLayout()
        csv_row.addWidget(self.csv_edit, 1)
        csv_row.addWidget(self.open_btn)
        csv_row.addWidget(self.new_btn)
        csv_row.addWidget(self.reload_btn)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #c0392b;")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        csv_box = QGroupBox("CSV log file")
        cb = QVBoxLayout(csv_box)
        cb.addLayout(csv_row)
        cb.addWidget(self.error_label)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("*001#")
        self.code_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^\*?\d{0,3}#?$"))
        )
        self.nickname_edit = QLineEdit()
        self.nickname_edit.setPlaceholderText("Programmed onto the radio")
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Optional, logged only")
        self.note_edit.setToolTip(
            "Stored in the DTMF CSV only. Not programmed onto the radio."
        )
        for edit in (self.code_edit, self.nickname_edit, self.note_edit):
            edit.textChanged.connect(self._update_enablement)
        self.add_warning = QLabel()
        self.add_warning.setStyleSheet("color: #c0392b;")
        self.add_warning.setWordWrap(True)
        self.add_warning.setVisible(False)
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self._add_entry)
        add_form = QFormLayout()
        add_form.addRow("Code:", self.code_edit)
        add_form.addRow("Nickname:", self.nickname_edit)
        add_form.addRow("Note:", self.note_edit)
        add_btn_row = QHBoxLayout()
        add_btn_row.addWidget(self.add_warning, 1)
        add_btn_row.addWidget(self.add_btn)
        self.add_box = QGroupBox("Add entry (without programming a radio)")
        ab = QVBoxLayout(self.add_box)
        ab.addLayout(add_form)
        ab.addLayout(add_btn_row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Code", "Nickname", "Note"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._update_enablement)
        self.table.cellDoubleClicked.connect(lambda *_: self._edit_note())
        self.edit_btn = QPushButton("Edit note...")
        self.remove_btn = QPushButton("Remove")
        self.edit_btn.clicked.connect(self._edit_note)
        self.remove_btn.clicked.connect(self._remove_entry)
        table_btn_row = QHBoxLayout()
        table_btn_row.addStretch(1)
        table_btn_row.addWidget(self.edit_btn)
        table_btn_row.addWidget(self.remove_btn)
        self.table_box = QGroupBox("Entries")
        tb = QVBoxLayout(self.table_box)
        tb.addWidget(self.table)
        tb.addLayout(table_btn_row)

        layout = QVBoxLayout(self)
        layout.addWidget(csv_box)
        layout.addWidget(self.add_box)
        layout.addWidget(self.table_box, 1)

        self._update_enablement()

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
        path = self.csv_path()
        self._entries = []
        self._error = None
        if path:
            try:
                self._entries = radijator.load_dtmf_log(path)
            except radijator.DtmfLogError as e:
                self._error = f"{e}\nFix the file by hand, then Reload."
            except OSError as e:
                self._error = f"Cannot read {path}: {e}"
        self._show_entries()

    def _show_entries(self, select_code: str | None = None):
        self.error_label.setText(self._error or "")
        self.error_label.setVisible(self._error is not None)
        self.table.setRowCount(len(self._entries))
        for r, e in enumerate(self._entries):
            self.table.setItem(r, 0, QTableWidgetItem(e.code))
            self.table.setItem(r, 1, QTableWidgetItem(e.nickname))
            self.table.setItem(r, 2, QTableWidgetItem(e.note))
            if e.code == select_code:
                self.table.selectRow(r)
        self.table_box.setTitle(f"Entries ({len(self._entries)})")
        code = self.code_edit.text().strip()
        if not radijator.DTMF_CODE_RE.match(code) or code in self.existing_codes():
            self.code_edit.setText(self.next_code() or "")
        self._update_enablement()
        self.csv_changed.emit()

    def _selected_entry(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return self._entries[rows[0].row()]

    def _update_enablement(self):
        code = self.code_edit.text().strip()
        duplicate = bool(radijator.DTMF_CODE_RE.match(code)) and (
            code in self.existing_codes()
        )
        self.code_edit.setStyleSheet("background-color: #f5b7b1;" if duplicate else "")
        self.add_warning.setText(f"{code} is already in the log." if duplicate else "")
        self.add_warning.setVisible(duplicate)

        usable = bool(self.csv_path()) and self._error is None and not self._running
        self.add_box.setEnabled(usable)
        self.add_btn.setEnabled(
            usable
            and bool(radijator.DTMF_CODE_RE.match(code))
            and not duplicate
            and bool(self.nickname_edit.text().strip())
        )
        selected = usable and self._selected_entry() is not None
        self.edit_btn.setEnabled(selected)
        self.remove_btn.setEnabled(selected)
        for btn in (self.open_btn, self.new_btn):
            btn.setEnabled(not self._running)
        self.reload_btn.setEnabled(bool(self.csv_path()) and not self._running)

    def _mutate(self, fn, *args, select_code: str | None = None) -> bool:
        try:
            self._entries = fn(self.csv_path(), *args)
        except radijator.DtmfLogError as e:
            QMessageBox.warning(self, "DTMF log", str(e))
            self.refresh_table()
            return False
        except OSError as e:
            QMessageBox.warning(self, "Cannot write CSV", str(e))
            return False
        self._show_entries(select_code)
        return True

    def _add_entry(self):
        code = self.code_edit.text().strip()
        if self._mutate(
            radijator.add_dtmf_entry,
            code,
            self.nickname_edit.text(),
            self.note_edit.text(),
        ):
            self.nickname_edit.clear()
            self.note_edit.clear()
            self.code_edit.setText(self.next_code() or "")

    def _edit_note(self):
        entry = self._selected_entry()
        if entry is None or not self.edit_btn.isEnabled():
            return
        text, ok = QInputDialog.getText(
            self,
            "Edit note",
            f"Note for {entry.code} ({entry.nickname}):",
            text=entry.note,
        )
        if ok:
            self._mutate(
                radijator.update_dtmf_note,
                entry.code,
                text,
                select_code=entry.code,
            )

    def _remove_entry(self):
        entry = self._selected_entry()
        if entry is None:
            return
        answer = QMessageBox.question(
            self,
            "Remove entry",
            f"Remove {entry.code} ({entry.nickname}) from the log? "
            "The radio keeps its code.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self._mutate(radijator.remove_dtmf_entry, entry.code)

    def existing_codes(self) -> set:
        return {e.code for e in self._entries}

    def next_code(self) -> str | None:
        return radijator.next_dtmf_code(self._entries)

    def has_error(self) -> bool:
        return self._error is not None

    def csv_path(self) -> str:
        return self.csv_edit.text().strip()

    def set_running(self, running: bool):
        self._running = running
        self._update_enablement()
