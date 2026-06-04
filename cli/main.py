"""CLI entry point: argparse setup, dispatch, crash logger."""

import argparse

# Side-effect import: populates RADIO_MODEL_ID_CLASS_DICT before argparse
# uses it to build the --radio-model choices.
from . import drivers as _drivers  # noqa: F401
from .convert import handle_convert_command
from .dtmf import _validate_dtmf_code
from .program import handle_program_command
from .radio import RADIO_MODEL_ID_CLASS_DICT
from .random_dcs import handle_random_dcs_command


def main():
    # __version__ kept on the radijator entry shim for back-compat. Import
    # it lazily here so this module can also be imported standalone for
    # tests without circular issues.
    import radijator

    parser = argparse.ArgumentParser(
        description="Radijator - A comprehensive tool for radio programming and memory management.",
        prog="radijator",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {radijator.__version__}"
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
    program_parser.add_argument(
        "--dtmf-code",
        type=_validate_dtmf_code,
        help="DTMF code for this radio in *ddd# format (e.g. *042#). "
        "Requires --dtmf-nickname and --dtmf-csv.",
    )
    program_parser.add_argument(
        "--dtmf-nickname",
        help="Human-readable label for this DTMF code. "
        "Requires --dtmf-code and --dtmf-csv.",
    )
    program_parser.add_argument(
        "--dtmf-csv",
        help="Path to the DTMF log CSV (created if missing). "
        "Requires --dtmf-code and --dtmf-nickname.",
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
        dtmf_args = (
            getattr(args, "dtmf_code", None),
            getattr(args, "dtmf_nickname", None),
            getattr(args, "dtmf_csv", None),
        )
        if any(dtmf_args) and not all(dtmf_args):
            parser.error(
                "--dtmf-code, --dtmf-nickname and --dtmf-csv must be used together"
            )
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
