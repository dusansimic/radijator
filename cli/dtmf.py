"""DTMF code validation and the DTMF log CSV (code, nickname, note)."""

import argparse
import csv
import os
import re
from dataclasses import dataclass

DTMF_CODE_RE = re.compile(r"^\*\d{3}#$")
DTMF_CSV_HEADER = ["code", "nickname", "note"]
_REAL_NAME_HEADER = ["code", "nickname", "real_name"]
_LEGACY_HEADER = ["code", "nickname"]


class DtmfLogError(ValueError):
    pass


@dataclass(frozen=True)
class DtmfEntry:
    code: str
    nickname: str
    note: str = ""


def _validate_dtmf_code(value: str) -> str:
    if not DTMF_CODE_RE.match(value):
        raise argparse.ArgumentTypeError(f"DTMF code must match *ddd# (got {value!r})")
    return value


def dtmf_code_number(code: str) -> int:
    return int(code[1:4])


def _sorted(entries) -> list:
    return sorted(entries, key=lambda e: dtmf_code_number(e.code))


def _check_text(label: str, value: str):
    if "\n" in value or "\r" in value:
        raise DtmfLogError(f"{label} must be a single line")


def load_dtmf_log(csv_path: str) -> list:
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        return []
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        rows = list(enumerate(csv.reader(f), start=1))

    if rows and [c.strip() for c in rows[0][1]] in (
        DTMF_CSV_HEADER,
        _REAL_NAME_HEADER,
        _LEGACY_HEADER,
    ):
        rows = rows[1:]

    entries = []
    errors = []
    seen = {}
    for line, row in rows:
        cells = [c.strip() for c in row]
        if not any(cells):
            continue
        if len(cells) not in (2, 3):
            errors.append(f"line {line}: expected 2 or 3 columns, got {len(cells)}")
            continue
        code, nickname = cells[0], cells[1]
        note = cells[2] if len(cells) == 3 else ""
        if not DTMF_CODE_RE.match(code):
            errors.append(f"line {line}: bad code {code!r}")
            continue
        if not nickname:
            errors.append(f"line {line}: empty nickname for {code}")
            continue
        if code in seen:
            errors.append(
                f"line {line}: duplicate code {code} (also line {seen[code]})"
            )
            continue
        seen[code] = line
        entries.append(DtmfEntry(code, nickname, note))

    if errors:
        raise DtmfLogError(f"{csv_path}:\n" + "\n".join(errors))
    return _sorted(entries)


def save_dtmf_log(csv_path: str, entries) -> None:
    tmp_path = csv_path + ".tmp"
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(DTMF_CSV_HEADER)
        for e in _sorted(entries):
            writer.writerow([e.code, e.nickname, e.note])
    os.replace(tmp_path, csv_path)


def add_dtmf_entry(csv_path: str, code: str, nickname: str, note: str = ""):
    code, nickname, note = code.strip(), nickname.strip(), note.strip()
    if not DTMF_CODE_RE.match(code):
        raise DtmfLogError(f"DTMF code must match *ddd# (got {code!r})")
    if not nickname:
        raise DtmfLogError("nickname is required")
    _check_text("nickname", nickname)
    _check_text("note", note)
    entries = load_dtmf_log(csv_path)
    if any(e.code == code for e in entries):
        raise DtmfLogError(f"DTMF code {code} is already in {csv_path}")
    entries.append(DtmfEntry(code, nickname, note))
    save_dtmf_log(csv_path, entries)
    return _sorted(entries)


def update_dtmf_note(csv_path: str, code: str, note: str):
    note = note.strip()
    _check_text("note", note)
    entries = load_dtmf_log(csv_path)
    for i, e in enumerate(entries):
        if e.code == code:
            entries[i] = DtmfEntry(e.code, e.nickname, note)
            save_dtmf_log(csv_path, entries)
            return entries
    raise DtmfLogError(f"DTMF code {code} is not in {csv_path}")


def remove_dtmf_entry(csv_path: str, code: str):
    entries = load_dtmf_log(csv_path)
    remaining = [e for e in entries if e.code != code]
    if len(remaining) == len(entries):
        raise DtmfLogError(f"DTMF code {code} is not in {csv_path}")
    save_dtmf_log(csv_path, remaining)
    return remaining


def next_dtmf_code(entries) -> str | None:
    if not entries:
        return "*001#"
    n = max(dtmf_code_number(e.code) for e in entries) + 1
    return f"*{n:03d}#" if n <= 999 else None
