"""DTMF code validation, CSV log append, sequential increment."""

import argparse
import csv
import os
import re


DTMF_CODE_RE = re.compile(r"^\*\d{3}#$")


def _validate_dtmf_code(value: str) -> str:
    if not DTMF_CODE_RE.match(value):
        raise argparse.ArgumentTypeError(
            f"DTMF code must match *ddd# (got {value!r})"
        )
    return value


def _append_dtmf_row(csv_path: str, code: str, nickname: str, log_fn=print):
    fresh = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if fresh:
            writer.writerow(["code", "nickname"])
        writer.writerow([code, nickname])
    log_fn(f"Logged DTMF {code} ({nickname}) to {csv_path}")


def _next_dtmf_code(code: str) -> str:
    if not DTMF_CODE_RE.match(code):
        raise ValueError(f"bad DTMF code: {code!r}")
    n = (int(code[1:4]) + 1) % 1000
    return f"*{n:03d}#"
