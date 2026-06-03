from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup
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
from .dtmf_tab import DtmfTab
from .program_tab import ProgramTab
from .worker import Worker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Radijator {radijator.__version__}")
        self.resize(800, 700)

        self.program_tab = ProgramTab()
        self.convert_tab = ConvertTab()
        self.dtmf_tab = DtmfTab()
        self.program_tab.run_requested.connect(self._run_program)
        self.convert_tab.run_requested.connect(self._run_convert)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.program_tab, "Program")
        self.tabs.addTab(self.convert_tab, "Convert")

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
        splitter.addWidget(self.tabs)
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

        options_menu = self.menuBar().addMenu("&Options")
        self.msg_override_action = QAction("Override power-on &message", self)
        self.msg_override_action.setCheckable(True)
        self.msg_override_action.toggled.connect(
            self.program_tab.set_message_override_visible
        )
        options_menu.addAction(self.msg_override_action)

        self.dtmf_action = QAction("Configure &DTMF code", self)
        self.dtmf_action.setCheckable(True)
        self.dtmf_action.toggled.connect(self._toggle_dtmf_tab)
        options_menu.addAction(self.dtmf_action)

        opts_group = QActionGroup(self)
        opts_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
        opts_group.addAction(self.msg_override_action)
        opts_group.addAction(self.dtmf_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Radijator",
            f"<h3>Radijator {radijator.__version__}</h3>"
            "<p>Cross-platform GUI for flashing memories and settings "
            "to Baofeng / Radtel radios via CHIRP drivers.</p>"
            "<p><b>Author:</b> Dušan Simić</p>"
            "<p><b>License:</b> BSD 2-Clause</p>"
            "<p><b>Repository:</b> "
            '<a href="https://github.com/dusansimic/radijator">'
            "github.com/dusansimic/radijator</a></p>",
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

    def _toggle_dtmf_tab(self, checked: bool):
        idx = self.tabs.indexOf(self.dtmf_tab)
        if checked and idx == -1:
            self.tabs.addTab(self.dtmf_tab, "DTMF")
        elif not checked and idx != -1:
            self.tabs.removeTab(idx)
        self.program_tab.set_dtmf_visible(checked)
        if checked and not self.program_tab.dtmf_code():
            last = self.dtmf_tab.last_code()
            self.program_tab.set_dtmf_code(
                radijator._next_dtmf_code(last) if last else "*001#"
            )

    def _start_worker(self, target, kwargs, with_progress: bool):
        if self._worker and self._worker.isRunning():
            return
        self.log_view.clear()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Running...")
        self.program_tab.set_running(True)
        self.convert_tab.set_running(True)
        self.dtmf_tab.set_running(True)

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
        self.dtmf_tab.set_running(False)
        if ok and self.dtmf_action.isChecked():
            self.dtmf_tab.refresh_table()
            last = self.dtmf_tab.last_code()
            if last:
                self.program_tab.set_dtmf_code(radijator._next_dtmf_code(last))
            self.program_tab.clear_dtmf_nickname()

    def _run_program(self, kwargs: dict):
        if self.dtmf_action.isChecked():
            csv_path = self.dtmf_tab.csv_path()
            code = self.program_tab.dtmf_code()
            nickname = self.program_tab.dtmf_nickname()
            if not csv_path or not code or not nickname:
                QMessageBox.warning(
                    self,
                    "Missing input",
                    "DTMF requires a CSV file (DTMF tab), a valid *ddd# code "
                    "and a nickname.",
                )
                return
            if not radijator.DTMF_CODE_RE.match(code):
                QMessageBox.warning(
                    self, "Missing input", "DTMF code must match *ddd#."
                )
                return
            kwargs = {
                **kwargs,
                "dtmf_csv": csv_path,
                "dtmf_code": code,
                "dtmf_nickname": nickname,
            }
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
