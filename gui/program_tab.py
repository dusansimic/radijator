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
    ("print-settings", "Print settings"),
    ("load-profile", "Load profile"),
    ("load-memory", "Load memory"),
    ("load-profile-and-memory", "Load profile and memory"),
]


class ProgramTab(QWidget):
    run_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model_combo = QComboBox()
        for model_id in radijator.RADIO_MODEL_ID_CLASS_DICT.keys():
            self.model_combo.addItem(model_id)

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
        self.dtmf_code_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^\*\d{3}#$"))
        )
        self.dtmf_nickname_edit = QLineEdit()
        self.dtmf_nickname_edit.setPlaceholderText("Operator name")
        dtmf_form = QFormLayout()
        dtmf_form.addRow("Code:", self.dtmf_code_edit)
        dtmf_form.addRow("Nickname:", self.dtmf_nickname_edit)
        self.dtmf_box = QGroupBox("DTMF code")
        db = QVBoxLayout(self.dtmf_box)
        db.addLayout(dtmf_form)
        self.dtmf_box.setVisible(False)

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
            self.port_combo.addItem(p.device)
        if current:
            self.port_combo.setEditText(current)

    def _pick_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select profile JSON", "", "JSON (*.json)"
        )
        if path:
            self.profile_edit.setText(path)

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
        self.profile_box.setEnabled(mode in ("load-profile", "load-profile-and-memory"))
        self.memory_box.setEnabled(mode in ("load-memory", "load-profile-and-memory"))

    def _memory_paths(self):
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
                "memory_paths": self._memory_paths() or None,
                "verbose": self.verbose_check.isChecked(),
                "profile_overrides": overrides,
            }
        )

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

    def set_running(self, running: bool):
        self.run_btn.setEnabled(not running)
        self.dtmf_code_edit.setEnabled(not running)
        self.dtmf_nickname_edit.setEnabled(not running)
