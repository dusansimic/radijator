import argparse
from chirp.drivers.uv5r import BaofengUV5R, UV5R_POWER_LEVELS
from chirp.drivers.uv6r import UV6R
from chirp.drivers.baofeng_wp970i import UV9R
from chirp.drivers.mml_jc8810 import RT470XRadio, RT470Radio
from serial.tools import list_ports
from serial import Serial
from chirp.chirp_common import Memory, PowerLevel, Radio
from chirp.settings import RadioSettings, RadioSettingValue
import time
from typing import Iterable
import json


class RadijatorMemory:
    number: int = None
    name: str = None
    freq: int = None
    power_level: PowerLevel = None
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
            rdcs_code=data.get("rdcs_code", 23),
            tdcs_code=data.get("tdcs_code", 23),
            dcs_polarity=data.get("dcs_polarity", "NN"),
            mode=data.get("mode", "NFM"),
            tuning_step=data.get("tuning_step", 5.0),
        )


class RadijatorRadio:
    DEFAULT_POWER_LEVEL: PowerLevel = None
    RESET_TIME = None
    MEMORY_RANGE = None
    RADIJATOR_SETTINGS_PROFILE_ID = None

    radio: Radio = None
    _settings: RadioSettings = None

    def __init__(self, DRIVER_CLASS: Radio, serial_port: str):
        self.radio = DRIVER_CLASS(
            Serial(serial_port, baudrate=DRIVER_CLASS.BAUD_RATE, timeout=0.25)
        )
        features = self.radio.get_features()
        memory_bounds = features.memory_bounds
        lower_memory, upper_memory = memory_bounds[0], memory_bounds[1]
        self.MEMORY_RANGE = range(lower_memory, upper_memory + 1)

    def download_fw(self, wait_for_reset: bool = True):
        self.radio.sync_in()
        self._settings = self.radio.get_settings()
        if wait_for_reset:
            print(f"Wait {self.RESET_TIME} seconds for radio to reset...")
            time.sleep(self.RESET_TIME)

    def upload_fw(self):
        self.radio.sync_out()

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

    def set_settings_profile(self, profile_file_name: str):
        profile = self._transpose_settings_profile(profile_file_name)

        settings = self._settings

        settings_generator = settings.walk()
        for setting in settings_generator:
            if setting.get_name() in profile:
                profile_setting = profile[setting.get_name()]
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

    def set_memories(self, memories: Iterable[RadijatorMemory]):
        self._clear_memories()
        next_memory_number = 1
        for memory in memories:
            memory.number = next_memory_number
            next_memory_number += 1
            chirp_memory = RadijatorMemory.to_chirp_memory(memory)
            print(chirp_memory)
            self.radio.set_memory(chirp_memory)


class RadijatorUV5R(RadijatorRadio):
    """
    Supported models:
    - Baofeng UV-5R
    - Baofeng UV-5R Plus
    - Baofeng UV-5RA
    """

    def __init__(self, serial_port: str):
        super().__init__(BaofengUV5R, serial_port)
        self.DEFAULT_POWER_LEVEL = UV5R_POWER_LEVELS[0]
        self.RESET_TIME = 6
        self.RADIJATOR_SETTINGS_PROFILE_ID = "uv5r"


# TODO: Check if it works
# TODO: Add to profile
class RadijatorUV6R(RadijatorRadio):
    def __init__(self, serial_port: str):
        super().__init__(UV6R, serial_port)
        self.DEFAULT_POWER_LEVEL = UV6R.POWER_LEVELS[0]
        self.RESET_TIME = 6


# TODO: Check if it works
# TODO: Add to profile
class RadijatorUV9R(RadijatorRadio):
    def __init__(self, serial_port: str):
        super().__init__(UV9R, serial_port)
        self.DEFAULT_POWER_LEVEL = UV9R.POWER_LEVELS[0]
        self.RESET_TIME = 6


# TODO: Baofeng UV-82 variants
# TODO: Baofeng UV-17 variants
# TODO: Baofeng UV-21 variants


# TODO: Fix Radio returned unknown identification string
# TODO: Add to profile
class RadijatorRT470X(RadijatorRadio):
    def __init__(self, serial_port):
        super().__init__(RT470XRadio, serial_port)
        self.DEFAULT_POWER_LEVEL = RT470XRadio.POWER_LEVELS[0]
        self.RESET_TIME = 3


# TODO: Check if it works
# TODO: Add to profile
class RadijatorRT470(RadijatorRadio):
    def __init__(self, serial_port):
        super().__init__(RT470Radio, serial_port)
        self.DEFAULT_POWER_LEVEL = RT470Radio.POWER_LEVELS[0]
        self.RESET_TIME = 3


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
        required=True,
        help="Serial port of the radio (e.g., COM3 or /dev/ttyUSB0).",
    )
    parser.add_argument(
        "-R",
        "--radio-model",
        required=True,
        choices=["uv5r", "uv6r", "rt470x", "rt470"],
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

    args = parser.parse_args()

    radio: RadijatorRadio = {
        "uv5r": RadijatorUV5R,
        "uv6r": RadijatorUV6R,
        "rt470x": RadijatorRT470X,
        "rt470": RadijatorRT470,
    }[args.radio_model](args.port)

    radio.download_fw(wait_for_reset=args.command != "print-settings")

    if args.command == "load-profile" or args.command == "load-profile-and-memory":
        if not args.profile:
            parser.error(
                "The --profile argument is required for the load-profile command."
            )
        radio.set_settings_profile(args.profile)
    if args.command == "print-settings":
        radio.print_settings()
    if args.command == "load-memory" or args.command == "load-profile-and-memory":
        if not args.memory:
            parser.error(
                "The --memory argument is required for the load-memory command."
            )

        print(args.memory)
        memories = []
        for memory_file in args.memory:
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for mem_data in data:
                    memories.append(
                        RadijatorMemory.from_json(mem_data, radio.DEFAULT_POWER_LEVEL)
                    )

        radio.set_memories(memories)

    if args.command != "print-settings":
        radio.upload_fw()


if __name__ == "__main__":
    main_radijator_cli()
