from PySide6.QtCore import QRegularExpression, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from serial.tools import list_ports

import radijator

MODES = [
    ("print-settings", "Print settings (read)"),
    ("download-profile", "Download profile (from device)"),
    ("upload-profile", "Upload profile (to device)"),
    ("download-memory", "Download memory (from device)"),
    ("upload-memory", "Upload memory (to device)"),
    ("load-profile-and-memory", "Upload profile + memory (to device)"),
]

PROFILE_MODES = ("download-profile", "upload-profile", "load-profile-and-memory")
MEMORY_MODES = ("upload-memory", "load-profile-and-memory")
DOWNLOAD_MODES = ("download-profile", "download-memory")
UPLOAD_MODES = ("upload-profile", "upload-memory", "load-profile-and-memory")


class ProgramTab(QWidget):
    run_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model_combo = QComboBox()
        for model_id in radijator.RADIO_MODEL_ID_CLASS_DICT.keys():
            self.model_combo.addItem(model_id)

        self._filter_usb_only = True
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self._refresh_ports()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_ports)
        port_row = QHBoxLayout()
        port_row.addWidget(self.port_combo, 1)
        port_row.addWidget(refresh_btn)

        self.mode_combo = QComboBox()
        for value, label in MODES:
            self.mode_combo.addItem(label, value)
        self.mode_combo.currentIndexChanged.connect(self._update_enablement)

        self.verbose_check = QCheckBox("Verbose")

        form = QFormLayout()
        form.addRow("Radio model:", self.model_combo)
        form.addRow("Serial port:", port_row)
        form.addRow("Operation:", self.mode_combo)
        form.addRow("", self.verbose_check)

        self.profile_edit = QLineEdit()
        self.profile_edit.setPlaceholderText("Settings profile JSON")
        profile_browse = QPushButton("Browse...")
        profile_browse.clicked.connect(self._pick_profile)
        profile_row = QHBoxLayout()
        profile_row.addWidget(self.profile_edit, 1)
        profile_row.addWidget(profile_browse)
        profile_box = QGroupBox("Profile")
        pb = QVBoxLayout(profile_box)
        pb.addLayout(profile_row)
        self.profile_box = profile_box

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Destination JSON file")
        output_browse = QPushButton("Browse...")
        output_browse.clicked.connect(self._pick_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(output_browse)
        self.output_box = QGroupBox("Output file")
        ob = QVBoxLayout(self.output_box)
        ob.addLayout(output_row)
        self.output_box.setVisible(False)

        self.msg_line1_edit = QLineEdit()
        self.msg_line1_edit.setPlaceholderText("Message line 1")
        self.msg_line2_edit = QLineEdit()
        self.msg_line2_edit.setPlaceholderText("Message line 2")
        msg_form = QFormLayout()
        msg_form.addRow("Line 1:", self.msg_line1_edit)
        msg_form.addRow("Line 2:", self.msg_line2_edit)
        self.msg_override_box = QGroupBox("Power-on message override")
        mob = QVBoxLayout(self.msg_override_box)
        mob.addLayout(msg_form)
        self.msg_override_box.setVisible(False)

        self.dtmf_code_edit = QLineEdit()
        self.dtmf_code_edit.setPlaceholderText("*001#")
        self.dtmf_code_edit.setToolTip(
            "Starting DTMF code in *ddd# format; auto-increments after each flash"
        )
        self.dtmf_code_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^\*?\d{0,3}#?$"))
        )
        self.dtmf_code_edit.textChanged.connect(self._check_dtmf_duplicate)
        self.dtmf_nickname_edit = QLineEdit()
        self.dtmf_nickname_edit.setPlaceholderText("Operator name")
        self.dtmf_warning = QLabel()
        self.dtmf_warning.setStyleSheet("color: #c0392b;")
        self.dtmf_warning.setWordWrap(True)
        self.dtmf_warning.setVisible(False)
        dtmf_form = QFormLayout()
        dtmf_form.addRow("Code:", self.dtmf_code_edit)
        dtmf_form.addRow("Nickname:", self.dtmf_nickname_edit)
        self.dtmf_box = QGroupBox("DTMF code")
        db = QVBoxLayout(self.dtmf_box)
        db.addLayout(dtmf_form)
        db.addWidget(self.dtmf_warning)
        self.dtmf_box.setVisible(False)

        self._taken_dtmf_codes = set()
        self._dtmf_duplicate = False

        self.memory_list = QListWidget()
        mem_add = QPushButton("Add...")
        mem_remove = QPushButton("Remove")
        mem_add.clicked.connect(self._add_memory)
        mem_remove.clicked.connect(self._remove_memory)
        mem_btn_row = QHBoxLayout()
        mem_btn_row.addWidget(mem_add)
        mem_btn_row.addWidget(mem_remove)
        mem_btn_row.addStretch(1)
        memory_box = QGroupBox("Memory files (concatenated in order)")
        mb = QVBoxLayout(memory_box)
        mb.addWidget(self.memory_list)
        mb.addLayout(mem_btn_row)
        self.memory_box = memory_box

        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._emit_run)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(profile_box)
        layout.addWidget(self.output_box)
        layout.addWidget(self.msg_override_box)
        layout.addWidget(self.dtmf_box)
        layout.addWidget(memory_box)
        layout.addWidget(self.run_btn)
        layout.addStretch(1)

        self._update_enablement()

    def _refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        for p in list_ports.comports():
            if self._filter_usb_only and not p.device.startswith("/dev/ttyUSB"):
                continue
            self.port_combo.addItem(p.device)
        if current:
            self.port_combo.setEditText(current)

    def set_port_filter_usb_only(self, usb_only: bool):
        self._filter_usb_only = usb_only
        self._refresh_ports()

    def _pick_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select profile JSON", "", "JSON (*.json)"
        )
        if path:
            self.profile_edit.setText(path)

    def _pick_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Select output JSON", "", "JSON (*.json)"
        )
        if path:
            if not path.lower().endswith(".json"):
                path += ".json"
            self.output_edit.setText(path)

    def _add_memory(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select memory JSON", "", "JSON (*.json)"
        )
        for p in paths:
            self.memory_list.addItem(p)

    def _remove_memory(self):
        for item in self.memory_list.selectedItems():
            self.memory_list.takeItem(self.memory_list.row(item))

    def _update_enablement(self):
        mode = self.mode_combo.currentData()
        self.profile_box.setEnabled(mode in PROFILE_MODES)
        self.profile_box.setTitle(
            "Profile (schema to snapshot)" if mode == "download-profile" else "Profile"
        )
        self.output_box.setVisible(mode in DOWNLOAD_MODES)
        # memory_box stays interactive in every mode — the list also
        # feeds the Convert tab.

    def memory_paths(self):
        return [
            self.memory_list.item(i).text() for i in range(self.memory_list.count())
        ]

    def _emit_run(self):
        overrides = None
        if self.msg_override_box.isVisible():
            overrides = {
                "Message Line 1": self.msg_line1_edit.text(),
                "Message Line 2": self.msg_line2_edit.text(),
            }
        self.run_requested.emit(
            {
                "radio_model": self.model_combo.currentText(),
                "port": self.port_combo.currentText(),
                "mode": self.mode_combo.currentData(),
                "profile": self.profile_edit.text() or None,
                "memory_paths": self.memory_paths() or None,
                "output_path": self.output_edit.text().strip() or None,
                "verbose": self.verbose_check.isChecked(),
                "profile_overrides": overrides,
            }
        )

    def current_mode(self) -> str:
        return self.mode_combo.currentData()

    def set_message_override_visible(self, visible: bool):
        self.msg_override_box.setVisible(visible)

    def set_dtmf_visible(self, visible: bool):
        self.dtmf_box.setVisible(visible)

    def dtmf_code(self) -> str:
        return self.dtmf_code_edit.text().strip()

    def dtmf_nickname(self) -> str:
        return self.dtmf_nickname_edit.text().strip()

    def set_dtmf_code(self, code: str):
        self.dtmf_code_edit.setText(code)

    def clear_dtmf_nickname(self):
        self.dtmf_nickname_edit.clear()

    def set_taken_dtmf_codes(self, codes):
        self._taken_dtmf_codes = set(codes)
        self._check_dtmf_duplicate()

    def dtmf_is_duplicate(self) -> bool:
        return self._dtmf_duplicate

    def _check_dtmf_duplicate(self):
        code = self.dtmf_code_edit.text().strip()
        self._dtmf_duplicate = (
            bool(radijator.DTMF_CODE_RE.match(code)) and code in self._taken_dtmf_codes
        )
        self.dtmf_code_edit.setStyleSheet(
            "background-color: #f5b7b1;" if self._dtmf_duplicate else ""
        )
        if self._dtmf_duplicate:
            self.dtmf_warning.setText(
                f"{code} is already assigned in the DTMF log — choose another."
            )
        self.dtmf_warning.setVisible(self._dtmf_duplicate)

    def set_running(self, running: bool):
        self.run_btn.setEnabled(not running)
        self.dtmf_code_edit.setEnabled(not running)
        self.dtmf_nickname_edit.setEnabled(not running)
