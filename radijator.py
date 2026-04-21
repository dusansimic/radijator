#!/usr/bin/env python3

import argparse
import json
import csv
import random
import time
from typing import Iterable

from chirp.drivers.uv5r import BaofengUV5R, BaofengUV82Radio
from chirp.drivers.uv6r import UV6R
from chirp.drivers.baofeng_wp970i import UV9R
from chirp.drivers.baofeng_uv17Pro import UV25, BFK5Plus
from chirp.drivers.mml_jc8810 import RT470XRadio, RT470Radio
from chirp.drivers.radtel_rt900 import RT900BT
from chirp.chirp_common import Memory, PowerLevel, Radio, DTCS_CODES as DCS_CODES
from chirp.settings import RadioSettings

# chirp.wxui.serialtrace hijacks sys.stdout/sys.stderr at import time,
# routing them into ~/.chirp/debug.log. Save and restore around the import.
import sys as _sys
_saved_stdout, _saved_stderr = _sys.stdout, _sys.stderr
from chirp.wxui.serialtrace import SerialTrace
_sys.stdout, _sys.stderr = _saved_stdout, _saved_stderr
del _sys, _saved_stdout, _saved_stderr

__version__ = "1.0.0"

# ============================================================================
# Radio Programming Classes (from radijator-cli.py)
# ============================================================================


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

    def download_fw(self, wait_for_reset: bool = True, log_fn=print):
        pipe = self._open_serial(self._serial_port)
        self.radio.set_pipe(pipe)
        self.radio.sync_in()
        self._settings = self.radio.get_settings()
        if wait_for_reset:
            log_fn(f"Wait {self.RESET_TIME} seconds for radio to reset...")
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

    def set_settings_profile(self, profile_file_name: str, verbose: bool, log_fn=print):
        profile = self._transpose_settings_profile(profile_file_name)

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
            if verbose:
                log_fn(str(chirp_memory))
            self.radio.set_memory(chirp_memory)
            if progress_fn:
                progress_fn(memory_number, total, "Writing memories")


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


# TODO: Add to profile
@register_radio
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
@register_radio
class RadijatorUV82(RadijatorRadio):
    DRIVER_CLASS = BaofengUV82Radio
    RADIJATOR_SETTINGS_PROFILE_ID = "uv82"


@register_radio
class RadijatorUV25(RadijatorRadio):
    DRIVER_CLASS = UV25
    RADIJATOR_SETTINGS_PROFILE_ID = "uv25"
    RESET_TIME = 4


# TODO: Fix issue with exception when logging
# TODO: Add to profile
class RadijatorK5Plus(RadijatorRadio):
    DRIVER_CLASS = BFK5Plus
    RADIJATOR_SETTINGS_PROFILE_ID = "k5plus"
    RESET_TIME = 4


# TODO: Baofeng UV-17 variants
# TODO: Baofeng UV-21 variants


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


# TODO: Fix issue with exception when logging
# TODO: Add to profile
@register_radio
class RadijatorRT900BT(RadijatorRadio):
    DRIVER_CLASS = RT900BT
    RADIJATOR_SETTINGS_PROFILE_ID = "rt900bt"
    RESET_TIME = 5


# ============================================================================
# Program subcommand functions (from radijator-cli.py)
# ============================================================================


def run_program(
    radio_model: str,
    port: str,
    mode: str,
    profile: str = None,
    memory_paths: Iterable[str] = None,
    verbose: bool = False,
    log_fn=print,
    progress_fn=None,
):
    """Core program workflow, usable by CLI and GUI.

    mode: one of "print-settings", "load-profile", "load-memory",
          "load-profile-and-memory".
    """
    if mode in ["load-profile", "load-profile-and-memory"] and not profile:
        raise ValueError("profile is required for load-profile / load-profile-and-memory")
    if mode in ["load-memory", "load-profile-and-memory"] and not memory_paths:
        raise ValueError("memory_paths is required for load-memory / load-profile-and-memory")

    radio: RadijatorRadio = RADIO_MODEL_ID_CLASS_DICT[radio_model](port)

    if progress_fn:
        progress_fn(0, 1, "Downloading from radio")
    log_fn("Downloading settings from radio...")
    radio.download_fw(wait_for_reset=mode != "print-settings", log_fn=log_fn)

    if mode in ["load-profile", "load-profile-and-memory"]:
        radio.set_settings_profile(profile, verbose, log_fn=log_fn)
    if mode == "print-settings":
        radio.print_settings(log_fn=log_fn)
    if mode in ["load-memory", "load-profile-and-memory"]:
        memories = []
        for memory_file in memory_paths:
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for mem_data in data:
                    memories.append(
                        RadijatorMemory.from_json(mem_data, radio.DEFAULT_POWER_LEVEL)
                    )

        radio.set_memories(memories, verbose, log_fn=log_fn, progress_fn=progress_fn)

    if mode != "print-settings":
        if progress_fn:
            progress_fn(1, 1, "Uploading to radio")
        log_fn("Uploading to radio...")
        radio.upload_fw()
        log_fn("Done.")


def handle_program_command(args):
    """Handle the 'program' subcommand with its nested subcommands."""
    run_program(
        radio_model=args.radio_model,
        port=args.port,
        mode=args.program_command,
        profile=getattr(args, "profile", None),
        memory_paths=getattr(args, "memory", None),
        verbose=args.verbose,
    )


# ============================================================================
# Convert subcommand functions (from json-to-chirp-csv.py)
# ============================================================================


def _to_chirp_format(memories):
    chirp_memories = []
    for location, memory in enumerate(memories, start=1):
        chirp_memory = {
            "Location": location,
            "Name": memory.get("name", ""),
            "Frequency": memory.get("frequency", 446000000) / 1e6,
            "Duplex": memory.get("duplex", ""),
            "Offset": memory.get("offset", 5000000) / 1e6,
            "Tone": memory.get("tone", ""),
            "rToneFreq": memory.get("rToneFreq", 88.5),
            "cToneFreq": memory.get("cToneFreq", 88.5),
            "DtcsCode": memory.get("tdcs_code", "023"),
            "DtcsPolarity": memory.get("dcs_polarity", "NN"),
            "RxDtcsCode": memory.get("rdcs_code", "023"),
            "CrossMode": memory.get("cross_mode", "Tone->Tone"),
            "Mode": memory.get("mode", "NFM"),
            "TStep": memory.get("tstep", "5.0"),
            "Skip": memory.get("skip", ""),
            "Power": memory.get("power", "50W"),
            "Comment": memory.get("comment", ""),
            "URCALL": memory.get("urcall", ""),
            "RPT1CALL": memory.get("rpt1call", ""),
            "RPT2CALL": memory.get("rpt2call", ""),
            "DVCODE": memory.get("dvcode", ""),
        }
        chirp_memories.append(chirp_memory)
    return chirp_memories


def run_convert(input_path: str, output_path: str, log_fn=print):
    """Core convert workflow, usable by CLI and GUI."""
    if not input_path:
        raise ValueError("Input file path is required.")
    if not output_path:
        raise ValueError("Output file path is required.")

    with open(input_path, "r", encoding="utf-8") as infile:
        memories = json.load(infile)

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        chirp_memories = _to_chirp_format(memories)
        writer = csv.DictWriter(csvfile, fieldnames=chirp_memories[0].keys())
        writer.writeheader()
        for memory in chirp_memories:
            writer.writerow(memory)

    log_fn(f"Converted {len(memories)} memories from {input_path} to {output_path}")


def handle_convert_command(args):
    """Handle the 'convert' subcommand."""
    run_convert(args.input, args.output)


# ============================================================================
# Random DCS subcommand functions (from random-dcs-assign.py)
# ============================================================================

DCS_POLARITIES = ["NN", "RR"]


def handle_random_dcs_command(args):
    """Handle the 'random-dcs' subcommand."""
    if not args.input:
        raise ValueError("Input file path is required.")
    if not args.output:
        raise ValueError("Output file path is required.")

    with open(args.input, "r", encoding="utf-8") as infile:
        memories = json.load(infile)

    for memory in memories:
        dcs_code = random.choice(DCS_CODES)
        dcs_polarity = random.choice(DCS_POLARITIES)
        memory["tone"] = "DTCS"
        memory["rdcs_code"] = dcs_code
        memory["tdcs_code"] = dcs_code
        memory["dcs_polarity"] = dcs_polarity

    with open(args.output, "w", encoding="utf-8") as outfile:
        json.dump(memories, outfile, ensure_ascii=False, indent=4)

    print(
        f"Assigned random DCS codes to {len(memories)} memories from {args.input} to {args.output}"
    )


# ============================================================================
# Main CLI Setup
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Radijator - A comprehensive tool for radio programming and memory management.",
        prog="radijator",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )

    # ========================================================================
    # Program subcommand with nested subcommands
    # ========================================================================
    program_parser = subparsers.add_parser(
        "program", help="Program radio settings and memories via serial connection"
    )

    # Add common arguments for all program subcommands
    program_parser.add_argument(
        "-p",
        "--port",
        help="Serial port of the radio (e.g., COM3 or /dev/ttyUSB0).",
        default="/dev/ttyUSB0",
    )
    program_parser.add_argument(
        "-R",
        "--radio-model",
        required=True,
        choices=RADIO_MODEL_ID_CLASS_DICT.keys(),
        help="Model of the radio.",
    )
    program_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output.",
    )

    # Create nested subparsers for program commands
    program_subparsers = program_parser.add_subparsers(
        dest="program_command", help="Program subcommands", required=True
    )

    # load-profile subcommand
    load_profile_parser = program_subparsers.add_parser(
        "load-profile", help="Load settings profile to radio"
    )
    load_profile_parser.add_argument(
        "-P",
        "--profile",
        required=True,
        help="Path to the settings profile JSON file.",
    )

    # print-settings subcommand
    program_subparsers.add_parser("print-settings", help="Print current radio settings")

    # load-memory subcommand
    load_memory_parser = program_subparsers.add_parser(
        "load-memory", help="Load memory channels to radio"
    )
    load_memory_parser.add_argument(
        "-M",
        "--memory",
        required=True,
        help="Path to the memory JSON file.",
        action="append",
    )

    # load-profile-and-memory subcommand
    load_both_parser = program_subparsers.add_parser(
        "load-profile-and-memory",
        help="Load both settings profile and memory channels to radio",
    )
    load_both_parser.add_argument(
        "-P",
        "--profile",
        required=True,
        help="Path to the settings profile JSON file.",
    )
    load_both_parser.add_argument(
        "-M",
        "--memory",
        required=True,
        help="Path to the memory JSON file.",
        action="append",
    )

    # ========================================================================
    # Convert subcommand
    # ========================================================================
    convert_parser = subparsers.add_parser(
        "convert", help="Convert JSON memory files to CHIRP CSV format"
    )
    convert_parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the input JSON file containing memories.",
    )
    convert_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to the output CSV file to save CHIRP formatted memories.",
    )

    # ========================================================================
    # Random DCS subcommand
    # ========================================================================
    random_dcs_parser = subparsers.add_parser(
        "random-dcs", help="Assign random DCS codes and polarities to memory channels"
    )
    random_dcs_parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the input JSON file containing memories.",
    )
    random_dcs_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to the output JSON file to save updated memories.",
    )

    # ========================================================================
    # Parse and dispatch
    # ========================================================================
    args = parser.parse_args()

    if args.command == "program":
        handle_program_command(args)
    elif args.command == "convert":
        handle_convert_command(args)
    elif args.command == "random-dcs":
        handle_random_dcs_command(args)


def _log_crash(exc, name: str):
    import os
    import sys
    import tempfile
    import traceback

    path = os.path.join(tempfile.gettempdir(), f"{name}-crash.log")
    try:
        with open(path, "w") as f:
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
        sys.stderr.write(f"Crash log written to {path}\n")
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException as e:
        _log_crash(e, "radijator")
        raise
