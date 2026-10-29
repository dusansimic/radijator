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
from .program_tab import (
    DOWNLOAD_MODES,
    MEMORY_MODES,
    PROFILE_MODES,
    UPLOAD_MODES,
    ProgramTab,
)
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
        self.dtmf_tab.csv_changed.connect(self._sync_taken_dtmf_codes)

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

        # macOS Qt's TextHeuristicRole moves actions whose text looks like
        # "Configure...", "Preferences", "Settings", etc. into the native
        # application menu, where they sometimes vanish. Pin every Options
        # entry to NoRole to keep them in the regular menu we put them in.
        options_menu = self.menuBar().addMenu("&Options")
        self.msg_override_action = QAction("Override power-on &message", self)
        self.msg_override_action.setCheckable(True)
        self.msg_override_action.setMenuRole(QAction.MenuRole.NoRole)
        self.msg_override_action.toggled.connect(
            self.program_tab.set_message_override_visible
        )
        options_menu.addAction(self.msg_override_action)

        self.dtmf_action = QAction("Configure &DTMF code", self)
        self.dtmf_action.setCheckable(True)
        self.dtmf_action.setMenuRole(QAction.MenuRole.NoRole)
        self.dtmf_action.toggled.connect(self._toggle_dtmf_tab)
        options_menu.addAction(self.dtmf_action)

        opts_group = QActionGroup(self)
        opts_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
        opts_group.addAction(self.msg_override_action)
        opts_group.addAction(self.dtmf_action)

        options_menu.addSeparator()
        self.show_all_ports_action = QAction("Show &all serial ports", self)
        self.show_all_ports_action.setCheckable(True)
        self.show_all_ports_action.setMenuRole(QAction.MenuRole.NoRole)
        self.show_all_ports_action.toggled.connect(
            lambda checked: self.program_tab.set_port_filter_usb_only(not checked)
        )
        options_menu.addAction(self.show_all_ports_action)

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
        if checked:
            self._sync_taken_dtmf_codes()

    def _sync_taken_dtmf_codes(self):
        taken = self.dtmf_tab.existing_codes()
        self.program_tab.set_taken_dtmf_codes(taken)
        code = self.program_tab.dtmf_code()
        if not code or code in taken:
            self.program_tab.set_dtmf_code(self.dtmf_tab.next_code() or "")

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
        if (
            ok
            and self.dtmf_action.isChecked()
            and self.program_tab.current_mode() in UPLOAD_MODES
        ):
            self.dtmf_tab.refresh_table()
            self.program_tab.set_dtmf_code(self.dtmf_tab.next_code() or "")
            self.program_tab.clear_dtmf_identity()

    def _run_program(self, kwargs: dict):
        mode = kwargs.get("mode")
        if mode in UPLOAD_MODES and self.dtmf_action.isChecked():
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
            self.dtmf_tab.refresh_table()
            if self.dtmf_tab.has_error():
                QMessageBox.warning(
                    self,
                    "DTMF log error",
                    "Fix the DTMF CSV first (see DTMF tab).",
                )
                return
            if code in self.dtmf_tab.existing_codes():
                QMessageBox.warning(
                    self,
                    "Duplicate DTMF code",
                    f"{code} is already assigned in the DTMF log. "
                    "Choose a different code.",
                )
                return
            kwargs = {
                **kwargs,
                "dtmf_csv": csv_path,
                "dtmf_code": code,
                "dtmf_nickname": nickname,
                "dtmf_note": self.program_tab.dtmf_note(),
            }
        missing = self._validate_program(kwargs)
        if missing:
            QMessageBox.warning(self, "Missing input", missing)
            return
        self._start_worker(radijator.run_program, kwargs, with_progress=True)

    def _run_convert(self, kwargs: dict):
        input_paths = self.program_tab.memory_paths()
        output_path = kwargs.get("output_path")
        if not input_paths:
            QMessageBox.warning(
                self,
                "Missing input",
                "Select at least one memory file on the Program tab.",
            )
            return
        if not output_path:
            QMessageBox.warning(self, "Missing input", "Output CSV path is required.")
            return
        self._start_worker(
            radijator.run_convert,
            {"input_paths": input_paths, "output_path": output_path},
            with_progress=False,
        )

    @staticmethod
    def _validate_program(kwargs: dict) -> str:
        if not kwargs.get("port"):
            return "Serial port is required."
        if not kwargs.get("radio_model"):
            return "Radio model is required."
        mode = kwargs.get("mode")
        if mode in PROFILE_MODES and not kwargs.get("profile"):
            hint = (
                "Select the master settings profile JSON to snapshot."
                if mode == "download-profile"
                else "Profile JSON is required for this operation."
            )
            return hint
        if mode in MEMORY_MODES and not kwargs.get("memory_paths"):
            return "At least one memory JSON file is required for this operation."
        if mode in DOWNLOAD_MODES and not kwargs.get("output_path"):
            return "An output file path is required for this operation."
        return ""
