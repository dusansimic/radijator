import json
import random
import argparse
from chirp.chirp_common import DTCS_CODES as DCS_CODES

DCS_POLARITIES = ["NN", "RR"]


def main_random_dcs_assign():
    parser = argparse.ArgumentParser(
        description="Assign random DCS codes and polarities to memories."
    )
    parser.add_argument(
        "-i", "--input", help="Path to the input JSON file containing memories."
    )
    parser.add_argument(
        "-o", "--output", help="Path to the output JSON file to save updated memories."
    )
    args = parser.parse_args()

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


if __name__ == "__main__":
    main_random_dcs_assign()
