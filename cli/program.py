"""program subcommand: orchestrates download → modify → upload."""

import json
from typing import Iterable

from .dtmf import DTMF_CODE_RE, _append_dtmf_row
from .memory import RadijatorMemory
from .progress import cli_reporter
from .radio import RADIO_MODEL_ID_CLASS_DICT, RadijatorRadio


def run_program(
    radio_model: str,
    port: str,
    mode: str,
    profile: str = None,
    memory_paths: Iterable[str] = None,
    verbose: bool = False,
    log_fn=print,
    progress_fn=None,
    profile_overrides: dict = None,
    dtmf_code: str = None,
    dtmf_nickname: str = None,
    dtmf_csv: str = None,
):
    """Core program workflow, usable by CLI and GUI.

    mode: one of "print-settings", "load-profile", "load-memory",
          "load-profile-and-memory".
    """
    if mode in ["load-profile", "load-profile-and-memory"] and not profile:
        raise ValueError("profile is required for load-profile / load-profile-and-memory")
    if mode in ["load-memory", "load-profile-and-memory"] and not memory_paths:
        raise ValueError("memory_paths is required for load-memory / load-profile-and-memory")

    dtmf_active = any((dtmf_code, dtmf_nickname, dtmf_csv))
    if dtmf_active and not all((dtmf_code, dtmf_nickname, dtmf_csv)):
        raise ValueError(
            "dtmf_code, dtmf_nickname and dtmf_csv must all be set together"
        )
    if dtmf_code is not None and not DTMF_CODE_RE.match(dtmf_code):
        raise ValueError(f"DTMF code must match *ddd# (got {dtmf_code!r})")

    radio: RadijatorRadio = RADIO_MODEL_ID_CLASS_DICT[radio_model](port)

    log_fn("Downloading settings from radio...")
    radio.download_fw(
        wait_for_reset=mode != "print-settings",
        log_fn=log_fn,
        progress_fn=progress_fn,
    )

    if mode in ["load-profile", "load-profile-and-memory"]:
        radio.set_settings_profile(
            profile,
            verbose,
            log_fn=log_fn,
            profile_overrides=profile_overrides,
        )
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
        if dtmf_code:
            radio.set_dtmf_code(dtmf_code, log_fn=log_fn)
            width = getattr(radio, "POWERON_MSG_WIDTH", 7)
            line1 = (dtmf_nickname or "")[:width].center(width)
            digits = "".join(c for c in dtmf_code if c.isdigit())
            line2 = digits[:width].center(width)
            radio.set_power_on_message(line1, line2, log_fn=log_fn)

        log_fn("Uploading to radio...")
        radio.upload_fw(log_fn=log_fn, progress_fn=progress_fn)
        log_fn("Done.")

        if dtmf_active:
            _append_dtmf_row(dtmf_csv, dtmf_code, dtmf_nickname, log_fn=log_fn)


def handle_program_command(args):
    """Handle the 'program' subcommand with its nested subcommands."""
    with cli_reporter() as (log_fn, progress_fn):
        run_program(
            radio_model=args.radio_model,
            port=args.port,
            mode=args.program_command,
            profile=getattr(args, "profile", None),
            memory_paths=getattr(args, "memory", None),
            verbose=args.verbose,
            log_fn=log_fn,
            progress_fn=progress_fn,
            dtmf_code=getattr(args, "dtmf_code", None),
            dtmf_nickname=getattr(args, "dtmf_nickname", None),
            dtmf_csv=getattr(args, "dtmf_csv", None),
        )
