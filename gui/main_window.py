from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import radijator

from .convert_tab import ConvertTab
from .program_tab import ProgramTab
from .worker import Worker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Radijator {radijator.__version__}")
        self.resize(800, 700)

        self.program_tab = ProgramTab()
        self.convert_tab = ConvertTab()
        self.program_tab.run_requested.connect(self._run_program)
        self.convert_tab.run_requested.connect(self._run_convert)

        tabs = QTabWidget()
        tabs.addTab(self.program_tab, "Program")
        tabs.addTab(self.convert_tab, "Convert")

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Idle")

        bottom = QWidget()
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(self.log_view, 1)
        bl.addWidget(self.progress_bar)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(tabs)
        splitter.addWidget(bottom)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

        self._build_menu()
        self._worker: Worker | None = None

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        quit_action = QAction("&Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Radijator",
            f"Radijator {radijator.__version__}\n\n"
            "Cross-platform GUI for flashing memories and settings\n"
            "to Baofeng / Radtel radios via CHIRP drivers.",
        )

    def _append_log(self, text: str):
        self.log_view.appendPlainText(text)

    def _on_progress(self, step: int, total: int, label: str):
        if total <= 0:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(step)
        self.progress_bar.setFormat(f"{label} ({step}/{total})" if total else label)

    def _start_worker(self, target, kwargs, with_progress: bool):
        if self._worker and self._worker.isRunning():
            return
        self.log_view.clear()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Running...")
        self.program_tab.set_running(True)
        self.convert_tab.set_running(True)

        self._worker = Worker(target, kwargs, with_progress=with_progress)
        self._worker.log.connect(self._append_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_with_result.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, ok: bool, message: str):
        self._append_log(f"\n=== {message} ===")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1 if ok else 0)
        self.progress_bar.setFormat("Done" if ok else "Failed")
        self.program_tab.set_running(False)
        self.convert_tab.set_running(False)

    def _run_program(self, kwargs: dict):
        missing = self._validate_program(kwargs)
        if missing:
            QMessageBox.warning(self, "Missing input", missing)
            return
        self._start_worker(radijator.run_program, kwargs, with_progress=True)

    def _run_convert(self, kwargs: dict):
        if not kwargs.get("input_path") or not kwargs.get("output_path"):
            QMessageBox.warning(self, "Missing input", "Input and output paths are required.")
            return
        self._start_worker(radijator.run_convert, kwargs, with_progress=False)

    @staticmethod
    def _validate_program(kwargs: dict) -> str:
        if not kwargs.get("port"):
            return "Serial port is required."
        if not kwargs.get("radio_model"):
            return "Radio model is required."
        mode = kwargs.get("mode")
        if mode in ("load-profile", "load-profile-and-memory") and not kwargs.get("profile"):
            return "Profile JSON is required for this operation."
        if mode in ("load-memory", "load-profile-and-memory") and not kwargs.get("memory_paths"):
            return "At least one memory JSON file is required for this operation."
        return ""
