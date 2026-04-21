from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ConvertTab(QWidget):
    run_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Input JSON")
        input_browse = QPushButton("Browse...")
        input_browse.clicked.connect(self._pick_input)
        input_row = QHBoxLayout()
        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(input_browse)

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Output CSV")
        output_browse = QPushButton("Browse...")
        output_browse.clicked.connect(self._pick_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(output_browse)

        form = QFormLayout()
        form.addRow("Input JSON:", input_row)
        form.addRow("Output CSV:", output_row)

        self.run_btn = QPushButton("Convert")
        self.run_btn.clicked.connect(self._emit_run)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.run_btn)
        layout.addStretch(1)

    def _pick_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Input JSON", "", "JSON (*.json)"
        )
        if path:
            self.input_edit.setText(path)

    def _pick_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Output CSV", "", "CSV (*.csv)"
        )
        if path:
            self.output_edit.setText(path)

    def _emit_run(self):
        self.run_requested.emit(
            {
                "input_path": self.input_edit.text(),
                "output_path": self.output_edit.text(),
            }
        )

    def set_running(self, running: bool):
        self.run_btn.setEnabled(not running)
