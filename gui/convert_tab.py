from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ConvertTab(QWidget):
    run_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        info = QLabel(
            "Inputs are the memory files selected on the Program tab. "
            "Pick an output CSV here, then click Convert."
        )
        info.setWordWrap(True)

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Output CSV")
        output_browse = QPushButton("Browse...")
        output_browse.clicked.connect(self._pick_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(output_browse)

        form = QFormLayout()
        form.addRow("Output CSV:", output_row)

        self.run_btn = QPushButton("Convert")
        self.run_btn.clicked.connect(self._emit_run)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addLayout(form)
        layout.addWidget(self.run_btn)
        layout.addStretch(1)

    def _pick_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Output CSV", "", "CSV (*.csv)")
        if path:
            self.output_edit.setText(path)

    def _emit_run(self):
        self.run_requested.emit({"output_path": self.output_edit.text()})

    def set_running(self, running: bool):
        self.run_btn.setEnabled(not running)
