"""RadijatorRadio base class and driver registry."""

import json
import time
from typing import Iterable

from chirp.chirp_common import Memory, PowerLevel, Radio
from chirp.settings import RadioSettings
from chirp.wxui.serialtrace import SerialTrace

from .memory import RadijatorMemory


class RadijatorRadio:
    DRIVER_CLASS: Radio = None
    DEFAULT_POWER_LEVEL: PowerLevel = None
    RESET_TIME = None
    MEMORY_RANGE = None
    RADIJATOR_SETTINGS_PROFILE_ID = None

    radio: Radio = None
    _settings: RadioSettings = None
    _serial_port: str = None

    def __init__(self, serial_port: str):
        self.radio = self.DRIVER_CLASS(None)
        self._serial_port = serial_port
        self._progress_fn = None
        self.radio.status_fn = self._on_chirp_status
        features = self.radio.get_features()
        memory_bounds = features.memory_bounds
        lower_memory, upper_memory = memory_bounds[0], memory_bounds[1]
        self.MEMORY_RANGE = range(lower_memory, upper_memory + 1)
        self.DEFAULT_POWER_LEVEL = features.valid_power_levels[0]

    def _on_chirp_status(self, status):
        if self._progress_fn is not None:
            self._progress_fn(status.cur, status.max, status.msg)

    def _open_serial(self, serial_port: str) -> SerialTrace:
        serial_object = SerialTrace(
            baudrate=self.DRIVER_CLASS.BAUD_RATE,
            rtscts=self.DRIVER_CLASS.HARDWARE_FLOW,
            timeout=0.25,
        )
        serial_object.rts = self.DRIVER_CLASS.WANTS_RTS
        serial_object.dtr = self.DRIVER_CLASS.WANTS_DTR
        serial_object.port = serial_port
        serial_object.open()
        return serial_object

    def _close_serial(self, serial: SerialTrace):
        serial.close()

    def download_fw(self, wait_for_reset: bool = True, log_fn=print, progress_fn=None):
        pipe = self._open_serial(self._serial_port)
        self.radio.set_pipe(pipe)
        self._progress_fn = progress_fn
        try:
            self.radio.sync_in()
        finally:
            self._progress_fn = None
        self._settings = self.radio.get_settings()
        if wait_for_reset:
            log_fn(f"Wait {self.RESET_TIME} seconds for radio to reset...")
            time.sleep(self.RESET_TIME)
        self._close_serial(pipe)

    def upload_fw(self, log_fn=print, progress_fn=None):
        pipe = self._open_serial(self._serial_port)
        self.radio.set_pipe(pipe)
        self._progress_fn = progress_fn
        try:
            self.radio.sync_out()
        finally:
            self._progress_fn = None
        self._close_serial(pipe)

    def _transpose_settings_profile(self, profile_file_name: str) -> dict:
        with open(profile_file_name, "r", encoding="utf-8") as f:
            profile = json.load(f)

        _profile = {}
        for setting_key, model_settings in profile.items():
            if self.RADIJATOR_SETTINGS_PROFILE_ID in model_settings:
                _profile[model_settings[self.RADIJATOR_SETTINGS_PROFILE_ID]["name"]] = {
                    "pretty_name": setting_key,
                    "value": model_settings[self.RADIJATOR_SETTINGS_PROFILE_ID][
                        "value"
                    ],
                }

        return _profile

    def set_settings_profile(
        self,
        profile_file_name: str,
        verbose: bool,
        log_fn=print,
        profile_overrides: dict = None,
    ):
        profile = self._transpose_settings_profile(profile_file_name)

        if profile_overrides:
            for entry in profile.values():
                pretty = entry["pretty_name"]
                if pretty in profile_overrides:
                    entry["value"] = profile_overrides[pretty]

        settings = self._settings

        log_fn("Applying settings profile...")
        settings_generator = settings.walk()
        for setting in settings_generator:
            if setting.get_name() in profile:
                profile_setting = profile[setting.get_name()]
                if verbose:
                    log_fn(
                        f"Setting {profile_setting['pretty_name']} to {profile_setting['value']}"
                    )
                setting.__setitem__(0, profile_setting["value"])

        self.radio.set_settings(settings)
        self._settings = self.radio.get_settings()

    def print_settings(self, log_fn=print):
        settings = self._settings

        settings_generator = settings.walk()
        for setting in settings_generator:
            log_fn(f"{setting.get_name()}: {setting.value}")

    def _clear_memories(self, progress_fn=None):
        total = len(self.MEMORY_RANGE)
        for step, i in enumerate(self.MEMORY_RANGE, start=1):
            mem = self.radio.get_memory(i)
            mem.empty = True
            self.radio.set_memory(mem)
            if progress_fn:
                progress_fn(step, total, "Clearing memories")

    def set_memories(
        self,
        memories: Iterable[RadijatorMemory],
        verbose: bool,
        log_fn=print,
        progress_fn=None,
    ):
        log_fn("Clearing existing memories...")
        self._clear_memories(progress_fn=progress_fn)
        log_fn("Setting new memories...")
        memories = list(memories)
        total = len(memories)
        for memory_number, memory in enumerate(memories, start=1):
            memory.number = memory_number
            chirp_memory = RadijatorMemory.to_chirp_memory(memory)
            self._apply_memory_extras(chirp_memory, memory)
            if verbose:
                log_fn(str(chirp_memory))
            self.radio.set_memory(chirp_memory)
            if progress_fn:
                progress_fn(memory_number, total, "Writing memories")

    def _apply_memory_extras(self, chirp_mem: Memory, rad_mem: RadijatorMemory):
        """Subclass hook to attach driver-specific Memory.extra entries
        (e.g. PTT-ID, BCL). Default: no-op."""
        pass

    def set_dtmf_code(self, code: str, log_fn=print):
        log_fn(
            f"set_dtmf_code not implemented for {self.__class__.__name__}; "
            f"requested code: {code}"
        )

    def set_power_on_message(self, line1: str, line2: str, log_fn=print):
        log_fn(
            f"set_power_on_message not implemented for "
            f"{self.__class__.__name__}; lines: {line1!r}, {line2!r}"
        )


RADIO_MODEL_ID_CLASS_DICT = {}


def register_radio(RADIO_CLASS):
    RADIO_MODEL_ID_CLASS_DICT[RADIO_CLASS.RADIJATOR_SETTINGS_PROFILE_ID] = RADIO_CLASS
    return RADIO_CLASS
