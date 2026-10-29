"""program subcommand: orchestrates download → modify → upload."""

import json
import os
from typing import Iterable

from .dtmf import DTMF_CODE_RE, add_dtmf_entry, load_dtmf_log
from .memory import RadijatorMemory
from .progress import cli_reporter
from .radio import RADIO_MODEL_ID_CLASS_DICT, RadijatorRadio

MODE_ALIASES = {
    "load-profile": "upload-profile",
    "load-memory": "upload-memory",
    "load-profile-and-memory": "upload-profile-and-memory",
}
_PROFILE_MODES = ("download-profile", "upload-profile", "upload-profile-and-memory")
_PROFILE_UPLOAD_MODES = ("upload-profile", "upload-profile-and-memory")
_MEMORY_UPLOAD_MODES = ("upload-memory", "upload-profile-and-memory")
_UPLOAD_MODES = ("upload-profile", "upload-memory", "upload-profile-and-memory")
_DOWNLOAD_MODES = ("download-profile", "download-memory")


def _write_json(path: str, data, log_fn=print):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    log_fn(f"Wrote {path}")


def run_program(
    radio_model: str,
    port: str,
    mode: str,
    profile: str = None,
    memory_paths: Iterable[str] = None,
    output_path: str = None,
    verbose: bool = False,
    log_fn=print,
    progress_fn=None,
    profile_overrides: dict = None,
    dtmf_code: str = None,
    dtmf_nickname: str = None,
    dtmf_csv: str = None,
    dtmf_real_name: str = "",
):
    """Core program workflow, usable by CLI and GUI.

    mode: one of "print-settings", "download-profile", "upload-profile",
          "download-memory", "upload-memory", "upload-profile-and-memory",
          or a legacy "load-*" alias from MODE_ALIASES.

    "download-*" reads the radio and writes a JSON file at output_path.
    "upload-*" apply the given JSON to the radio and clone it back.
    download-profile reuses "profile" as the master schema to snapshot.
    """
    mode = MODE_ALIASES.get(mode, mode)
    if mode in _PROFILE_MODES and not profile:
        raise ValueError(f"profile is required for {mode}")
    if mode in _MEMORY_UPLOAD_MODES and not memory_paths:
        raise ValueError(f"memory_paths is required for {mode}")
    if mode in _DOWNLOAD_MODES and not output_path:
        raise ValueError(f"output_path is required for {mode}")
    # The download holds only this model's entries; writing over the master
    # would drop every other model's settings.
    if mode == "download-profile" and os.path.realpath(output_path) == os.path.realpath(
        profile
    ):
        raise ValueError("output_path must differ from the master profile")

    dtmf_active = any((dtmf_code, dtmf_nickname, dtmf_csv))
    if dtmf_active and not all((dtmf_code, dtmf_nickname, dtmf_csv)):
        raise ValueError(
            "dtmf_code, dtmf_nickname and dtmf_csv must all be set together"
        )
    if dtmf_real_name and not dtmf_active:
        raise ValueError(
            "dtmf_real_name requires dtmf_code, dtmf_nickname and dtmf_csv"
        )
    if dtmf_code is not None and not DTMF_CODE_RE.match(dtmf_code):
        raise ValueError(f"DTMF code must match *ddd# (got {dtmf_code!r})")
    if dtmf_active and mode not in _UPLOAD_MODES:
        raise ValueError(f"DTMF options only apply to upload modes, not {mode}")
    # Load before touching the radio: a malformed log must not leave a
    # flashed radio that cannot be logged.
    if dtmf_active and dtmf_code in {e.code for e in load_dtmf_log(dtmf_csv)}:
        raise ValueError(f"DTMF code {dtmf_code} is already in {dtmf_csv}")

    radio: RadijatorRadio = RADIO_MODEL_ID_CLASS_DICT[radio_model](port)

    uploads = mode in _UPLOAD_MODES
    log_fn("Downloading settings from radio...")
    radio.download_fw(
        wait_for_reset=uploads,
        log_fn=log_fn,
        progress_fn=progress_fn,
    )

    if mode in _PROFILE_UPLOAD_MODES:
        radio.set_settings_profile(
            profile,
            verbose,
            log_fn=log_fn,
            profile_overrides=profile_overrides,
        )
    if mode == "print-settings":
        radio.print_settings(log_fn=log_fn)
    if mode == "download-profile":
        _write_json(
            output_path,
            radio.dump_settings_profile(profile, log_fn=log_fn),
            log_fn=log_fn,
        )
    if mode == "download-memory":
        _write_json(
            output_path,
            radio.dump_memories(log_fn=log_fn, progress_fn=progress_fn),
            log_fn=log_fn,
        )
    if mode in _MEMORY_UPLOAD_MODES:
        memories = []
        for memory_file in memory_paths:
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for mem_data in data:
                    memories.append(
                        RadijatorMemory.from_json(mem_data, radio.DEFAULT_POWER_LEVEL)
                    )

        radio.set_memories(memories, verbose, log_fn=log_fn, progress_fn=progress_fn)

    if uploads:
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
            add_dtmf_entry(dtmf_csv, dtmf_code, dtmf_nickname, dtmf_real_name or "")
            log_fn(f"Logged DTMF {dtmf_code} ({dtmf_nickname}) to {dtmf_csv}")


def handle_program_command(args):
    """Handle the 'program' subcommand with its nested subcommands."""
    with cli_reporter() as (log_fn, progress_fn):
        run_program(
            radio_model=args.radio_model,
            port=args.port,
            mode=args.program_command,
            profile=getattr(args, "profile", None),
            memory_paths=getattr(args, "memory", None),
            output_path=getattr(args, "output", None),
            verbose=args.verbose,
            log_fn=log_fn,
            progress_fn=progress_fn,
            dtmf_code=getattr(args, "dtmf_code", None),
            dtmf_nickname=getattr(args, "dtmf_nickname", None),
            dtmf_csv=getattr(args, "dtmf_csv", None),
            dtmf_real_name=getattr(args, "dtmf_real_name", None) or "",
        )
