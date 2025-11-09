#!/usr/bin/env python3

import argparse
from chirp.drivers.uv5r import BaofengUV5R, BaofengUV82Radio
from chirp.drivers.uv6r import UV6R
from chirp.drivers.baofeng_wp970i import UV9R
from chirp.drivers.baofeng_uv17Pro import UV25
from chirp.drivers.mml_jc8810 import RT470XRadio, RT470Radio
from serial import Serial
from chirp.chirp_common import Memory, PowerLevel, Radio
from chirp.settings import RadioSettings
import time
from typing import Iterable
import json


class RadijatorMemory:
    number: int = None
    name: str = None
    freq: int = None
    power_level: PowerLevel = None
    tone: str = None  # valid values: "", "DTCS"
    rdcs_code: int = None
    tdcs_code: int = None
    dcs_polarity: int = None
    mode: str = None
    tuning_step: float = None

    def __init__(
        self,
        number: int,
        name: str,
        freq: int,
        power_level: PowerLevel,
        tone: str = "",
        rdcs_code: int = 23,
        tdcs_code: int = 23,
        dcs_polarity: str = "NN",
        mode: str = "NFM",
        tuning_step: float = 5.0,
    ):
        self.number = number
        self.name = name
        self.freq = freq
        self.power_level = power_level
        self.tone = tone
        self.rdcs_code = rdcs_code
        self.tdcs_code = tdcs_code
        self.dcs_polarity = dcs_polarity
        self.mode = mode
        self.tuning_step = tuning_step

    def __str__(self):
        return f"Mem#{self.number} {self.name} Freq:{self.freq} Power:{self.power_level} RDCS:{self.rdcs_code} TDCS:{self.tdcs_code} DCS Polarity:{self.dcs_polarity}"

    @staticmethod
    def from_chirp_memory(mem: Memory) -> "RadijatorMemory":
        return RadijatorMemory(
            number=mem.number,
            name=mem.name,
            freq=mem.freq,
            power_level=mem.power,
            rdcs_code=mem.rx_dtcs,
            tdcs_code=mem.dtcs,
            dcs_polarity=mem.dtcs_polarity,
            mode=mem.mode,
            tuning_step=mem.tuning_step,
        )

    @staticmethod
    def to_chirp_memory(rad_mem: "RadijatorMemory") -> Memory:
        mem = Memory()
        mem.number = rad_mem.number
        mem.name = rad_mem.name
        mem.freq = rad_mem.freq
        mem.power = rad_mem.power_level
        mem.tmode = rad_mem.tone
        mem.rx_dtcs = rad_mem.rdcs_code
        mem.dtcs = rad_mem.tdcs_code
        mem.dtcs_polarity = rad_mem.dcs_polarity
        mem.mode = rad_mem.mode
        mem.tuning_step = rad_mem.tuning_step
        mem.duplex = ""
        mem.offset = 0
        mem.empty = False
        return mem

    @staticmethod
    def from_json(data: dict, power_level: PowerLevel) -> "RadijatorMemory":
        # TODO: Copilot generated, verify correctness
        return RadijatorMemory(
            number=data.get("number", None),
            name=data["name"],
            freq=data["frequency"],
            power_level=power_level,
            tone=data.get("tone", ""),
            rdcs_code=data.get("rdcs_code", 23),
            tdcs_code=data.get("tdcs_code", 23),
            dcs_polarity=data.get("dcs_polarity", "NN"),
            mode=data.get("mode", "NFM"),
            tuning_step=data.get("tuning_step", 5.0),
        )


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
        features = self.radio.get_features()
        memory_bounds = features.memory_bounds
        lower_memory, upper_memory = memory_bounds[0], memory_bounds[1]
        self.MEMORY_RANGE = range(lower_memory, upper_memory + 1)
        self.DEFAULT_POWER_LEVEL = features.valid_power_levels[0]

    def _open_serial(self, serial_port: str) -> Serial:
        serial_object = Serial(
            baudrate=self.DRIVER_CLASS.BAUD_RATE,
            rtscts=self.DRIVER_CLASS.HARDWARE_FLOW,
            timeout=0.25,
        )
        serial_object.rts = self.DRIVER_CLASS.WANTS_RTS
        serial_object.dtr = self.DRIVER_CLASS.WANTS_DTR
        serial_object.port = serial_port
        serial_object.open()
        return serial_object

    def _close_serial(self, serial: Serial):
        serial.close()

    def download_fw(self, wait_for_reset: bool = True):
        pipe = self._open_serial(self._serial_port)
        self.radio.set_pipe(pipe)
        self.radio.sync_in()
        self._settings = self.radio.get_settings()
        if wait_for_reset:
            print(f"Wait {self.RESET_TIME} seconds for radio to reset...")
            time.sleep(self.RESET_TIME)
        self._close_serial(pipe)

    def upload_fw(self):
        pipe = self._open_serial(self._serial_port)
        self.radio.set_pipe(pipe)
        self.radio.sync_out()
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

    def set_settings_profile(self, profile_file_name: str, verbose: bool):
        profile = self._transpose_settings_profile(profile_file_name)

        settings = self._settings

        print("Applying settings profile...")
        settings_generator = settings.walk()
        for setting in settings_generator:
            if setting.get_name() in profile:
                profile_setting = profile[setting.get_name()]
                if verbose:
                    print(
                        f"Setting {profile_setting['pretty_name']} to {profile_setting['value']}"
                    )
                setting.__setitem__(0, profile_setting["value"])

        self.radio.set_settings(settings)
        self._settings = self.radio.get_settings()

    def print_settings(self):
        settings = self._settings

        settings_generator = settings.walk()
        for setting in settings_generator:
            print(f"{setting.get_name()}: {setting.value}")

    def _clear_memories(self):
        for i in self.MEMORY_RANGE:
            mem = self.radio.get_memory(i)
            mem.empty = True
            self.radio.set_memory(mem)

    def set_memories(self, memories: Iterable[RadijatorMemory], verbose: bool):
        print("Clearing existing memories...")
        self._clear_memories()
        print("Setting new memories...")
        for memory_number, memory in enumerate(memories, start=1):
            memory.number = memory_number
            chirp_memory = RadijatorMemory.to_chirp_memory(memory)
            if verbose:
                print(chirp_memory)
            self.radio.set_memory(chirp_memory)


RADIO_MODEL_ID_CLASS_DICT = {}


def register_radio(RADIO_CLASS: RadijatorRadio):
    RADIO_MODEL_ID_CLASS_DICT[RADIO_CLASS.RADIJATOR_SETTINGS_PROFILE_ID] = RADIO_CLASS
    return RADIO_CLASS


@register_radio
class RadijatorUV5R(RadijatorRadio):
    """
    Supported models:
    - Baofeng UV-5R
    - Baofeng UV-5R Plus
    - Baofeng UV-5RA
    """

    DRIVER_CLASS = BaofengUV5R
    RADIJATOR_SETTINGS_PROFILE_ID = "uv5r"
    RESET_TIME = 6


# TODO: Check if it works
# TODO: Add to profile
class RadijatorUV6R(RadijatorRadio):
    DRIVER_CLASS = UV6R
    RADIJATOR_SETTINGS_PROFILE_ID = "uv6r"
    RESET_TIME = 6


# TODO: Check if it works
# TODO: Add to profile
class RadijatorUV9R(RadijatorRadio):
    DRIVER_CLASS = UV9R
    RADIJATOR_SETTINGS_PROFILE_ID = "uv9r"
    RESET_TIME = 6


# TODO: Check if it works
# TODO: Add to profile
class RadijatorUV82(RadijatorRadio):
    DRIVER_CLASS = BaofengUV82Radio
    RADIJATOR_SETTINGS_PROFILE_ID = "uv82"


@register_radio
class RadijatorUV25(RadijatorRadio):
    DRIVER_CLASS = UV25
    RADIJATOR_SETTINGS_PROFILE_ID = "uv25"
    RESET_TIME = 4


# TODO: Baofeng UV-82 variants
# TODO: Baofeng UV-17 variants
# TODO: Baofeng UV-21 variants
# TODO: Baofeng K5 Plus variants


@register_radio
class RadijatorRT470X(RadijatorRadio):
    DRIVER_CLASS = RT470XRadio
    RADIJATOR_SETTINGS_PROFILE_ID = "rt470x"
    RESET_TIME = 3


@register_radio
class RadijatorRT470(RadijatorRadio):
    DRIVER_CLASS = RT470Radio
    RADIJATOR_SETTINGS_PROFILE_ID = "rt470"
    RESET_TIME = 3


def main_radijator_cli():
    parser = argparse.ArgumentParser(
        description="Radijator CLI - A tool to manage radio settings and firmware."
    )
    parser.add_argument(
        "command",
        choices=[
            "load-profile",
            "print-settings",
            "load-memory",
            "load-profile-and-memory",
        ],
        help="Command to execute.",
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Serial port of the radio (e.g., COM3 or /dev/ttyUSB0).",
        default="/dev/ttyUSB0",
    )
    parser.add_argument(
        "-R",
        "--radio-model",
        required=True,
        choices=RADIO_MODEL_ID_CLASS_DICT.keys(),
        help="Model of the radio.",
    )
    parser.add_argument(
        "-P",
        "--profile",
        help="Path to the settings profile JSON file (required for set-profile command).",
    )
    parser.add_argument(
        "-M",
        "--memory",
        help="Path to the memory JSON file (required for load-memory command).",
        action="append",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output.",
    )

    args = parser.parse_args()

    # validate arguments
    if args.command in ["load-profile", "load-profile-and-memory"] and not args.profile:
        parser.error("The --profile argument is required for the load-profile command.")
    if args.command in ["load-memory", "load-profile-and-memory"] and not args.memory:
        parser.error("The --memory argument is required for the load-memory command.")

    # initialize radio class
    radio: RadijatorRadio = RADIO_MODEL_ID_CLASS_DICT[args.radio_model](args.port)

    # download firmware and settings
    radio.download_fw(wait_for_reset=args.command != "print-settings")

    if args.command in ["load-profile", "load-profile-and-memory"]:
        radio.set_settings_profile(args.profile, args.verbose)
    if args.command == "print-settings":
        radio.print_settings()
    if args.command in ["load-memory", "load-profile-and-memory"]:
        memories = []
        for memory_file in args.memory:
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for mem_data in data:
                    memories.append(
                        RadijatorMemory.from_json(mem_data, radio.DEFAULT_POWER_LEVEL)
                    )

        radio.set_memories(memories, args.verbose)

    if args.command != "print-settings":
        radio.upload_fw()


if __name__ == "__main__":
    main_radijator_cli()
