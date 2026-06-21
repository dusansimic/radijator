"""convert subcommand: Radijator memory JSON → CHIRP CSV."""

import csv
import json
from typing import Iterable


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
            "rToneFreq": memory.get("rtone", 88.5),
            "cToneFreq": memory.get("ctone", 88.5),
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


def run_convert(input_paths: Iterable[str], output_path: str, log_fn=print):
    """Core convert workflow, usable by CLI and GUI.

    Each input is a memory JSON (array of channels); they are
    concatenated in the order given before writing the CSV. Locations
    in the resulting CSV are sequential across the whole concatenation.
    """
    input_paths = list(input_paths or [])
    if not input_paths:
        raise ValueError("At least one input file path is required.")
    if not output_path:
        raise ValueError("Output file path is required.")

    memories = []
    for path in input_paths:
        with open(path, "r", encoding="utf-8") as infile:
            data = json.load(infile)
        log_fn(f"Loaded {len(data)} memories from {path}")
        memories.extend(data)

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        chirp_memories = _to_chirp_format(memories)
        writer = csv.DictWriter(csvfile, fieldnames=chirp_memories[0].keys())
        writer.writeheader()
        for memory in chirp_memories:
            writer.writerow(memory)

    log_fn(
        f"Converted {len(memories)} memories from "
        f"{len(input_paths)} file(s) to {output_path}"
    )


def handle_convert_command(args):
    """Handle the 'convert' subcommand."""
    run_convert(args.memory, args.output)
