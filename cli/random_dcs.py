"""random-dcs subcommand: assign random DCS codes to a memory JSON."""

import json
import random

from chirp.chirp_common import DTCS_CODES as DCS_CODES

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
