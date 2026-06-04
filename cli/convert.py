"""convert subcommand: Radijator memory JSON → CHIRP CSV."""

import csv
import json


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
