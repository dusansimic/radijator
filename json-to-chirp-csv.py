import argparse
import json
import csv


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


def jsontochirpcsvmain():
    parser = argparse.ArgumentParser(
        description="Convert JSON memories to CHIRP CSV format."
    )
    parser.add_argument(
        "-i", "--input", help="Path to the input JSON file containing memories."
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the output CSV file to save CHIRP formatted memories.",
    )
    args = parser.parse_args()

    if not args.input:
        raise ValueError("Input file path is required.")
    if not args.output:
        raise ValueError("Output file path is required.")

    with open(args.input, "r", encoding="utf-8") as infile:
        memories = json.load(infile)

    with open(args.output, "w", newline="", encoding="utf-8") as csvfile:
        chirp_memories = _to_chirp_format(memories)
        writer = csv.DictWriter(csvfile, fieldnames=chirp_memories[0].keys())
        writer.writeheader()
        for memory in chirp_memories:
            writer.writerow(memory)


if __name__ == "__main__":
    jsontochirpcsvmain()
