# radijator

A simple script for efficient flashing of settings and memory channels to Chinese shitbox mobile radios (e.g. Baofeng), plus helpers for generating random DCS codes and converting the radijator JSON format to CHIRP-compatible CSV.

Built on top of [CHIRP](https://chirpmyradio.com/) radio drivers.

## Features

- **Program radio over serial** — download firmware/settings from the radio, apply a settings profile and/or memory channels, and upload back.
- **Settings profiles** — single JSON file declares pretty-named settings once and maps them per radio model (squelch, power save, TOT, VOX, etc.). Reusable across models.
- **Memory channels** — load channels from one or more JSON files. Multiple `-M` files are concatenated in order.
- **Existing memories wiped** — before writing, all memory slots in the radio's memory range are cleared so leftover channels don't linger.
- **Print current settings** — dump every setting currently stored on the radio without mutating it.
- **JSON → CHIRP CSV conversion** — turn a radijator memory JSON file into a CSV importable by CHIRP.
- **Random DCS assignment** — batch-assign random DCS codes and polarities (NN/RR) to a memory JSON file, writing a new JSON.
- **Verbose mode** — log each setting applied and each memory written.

## Supported radios

Radio is selected with `-R <id>`. Currently registered:

| ID | Models | Driver |
|----|--------|--------|
| `uv5r` | Baofeng UV-5R, UV-5R Plus, UV-5RA | `BaofengUV5R` |
| `uv6r` | Baofeng UV-6R | `UV6R` |
| `uv82` | Baofeng UV-82 | `BaofengUV82Radio` |
| `uv25` | Baofeng UV-25 | `UV25` |
| `rt470` | Radtel RT-470 | `RT470Radio` |
| `rt470x` | Radtel RT-470X | `RT470XRadio` |
| `rt900bt` | Radtel RT-900BT | `RT900BT` |

Unregistered/WIP in source: `uv9r`, `k5plus` (driver present but `@register_radio` not applied — see TODOs in [radijator.py](radijator.py)).

## Commands

```
radijator <command> [options]
```

### `program` — flash radio over serial

Common flags:

- `-p, --port` — serial port (default `/dev/ttyUSB0`)
- `-R, --radio-model` — one of the IDs above (required)
- `--verbose` — log every setting and memory written

Nested subcommands:

| Subcommand | Purpose |
|------------|---------|
| `print-settings` | Download settings from radio and print them. No upload. |
| `load-profile -P <profile.json>` | Apply a settings profile. |
| `load-memory -M <mem.json> [-M <mem2.json> ...]` | Clear and write memory channels. |
| `load-profile-and-memory -P <profile.json> -M <mem.json> [-M ...]` | Both, in one serial session. |

Flow for non-`print-settings` commands: open serial → `sync_in` → apply profile/memories → `sync_out`. After download, waits `RESET_TIME` seconds (per-model, 3–6s) for the radio to reset before closing the port.

Example:

```sh
radijator program -p /dev/ttyUSB0 -R uv5r load-profile-and-memory \
    -P settings_profile.json -M memories/pmr.json --verbose
```

### `convert` — JSON → CHIRP CSV

```sh
radijator convert -i memories/pmr.json -o pmr.csv
```

Fills CHIRP fields (Location, Name, Frequency in MHz, Duplex, Offset, Tone, DTCS, Mode, Power, …) with defaults when missing.

### `random-dcs` — assign random DCS codes

```sh
radijator random-dcs -i memories/pmr.json -o memories/pmr-dcs.json
```

Sets `tone=DTCS`, random `rdcs_code`/`tdcs_code` (same pair) from `DTCS_CODES`, random polarity from `NN`/`RR`. Writes a new JSON.

## File formats

### Memory JSON (array of channels)

Minimum:

```json
[
  { "name": "PMR  1", "frequency": 446006250 }
]
```

Optional keys (defaults in parens): `number`, `tone` (`""`), `rdcs_code` (`23`), `tdcs_code` (`23`), `dcs_polarity` (`"NN"`), `mode` (`"NFM"`), `tuning_step` (`5.0`). Frequency is in Hz. Channel numbers are auto-assigned from 1 in array order.

`convert` accepts extra fields: `duplex`, `offset`, `rToneFreq`, `cToneFreq`, `cross_mode`, `tstep`, `skip`, `power`, `comment`, `urcall`, `rpt1call`, `rpt2call`, `dvcode`.

### Settings profile JSON

One pretty key per setting, then per-model `{name, value}` mapping. Missing model = setting skipped for that radio.

```json
{
  "Squelch Level": {
    "uv5r":  { "name": "squelch",          "value": 1 },
    "uv25":  { "name": "settings.squelch", "value": 1 },
    "rt470": { "name": "sql",              "value": 1 }
  }
}
```

`name` is the CHIRP setting path walked via `settings.walk()`. `value` is written with the setting's `__setitem__(0, value)`.

See [settings_profile.json](settings_profile.json) for a full example.

## Setting up

No clean install yet — hotwired against a CHIRP checkout.

Layout:

```
.
|- chirp       # cloned CHIRP repo
|- radijator   # this repo
```

Tested on Linux (Fedora 43). Should work elsewhere with minimal tweaks.

> [!CAUTION]
> On Linux, comment out `wxPython` in CHIRP's `requirements.txt` and install it from the system package manager.

```sh
cd chirp
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Wrapper script in `$PATH` (e.g. `$HOME/.local/bin/radijator`):

```bash
#!/bin/bash

BASE_DIRECTORY=/path/to/base/directory

source $BASE_DIRECTORY/chirp/.venv/bin/activate
export PYTHONPATH="$PYTHONPATH:$BASE_DIRECTORY/chirp:/usr/lib64/python3.14/site-packages"
python $BASE_DIRECTORY/radijator/radijator.py $@
deactivate
```

## License

BSD 2-clause license

## Author

Dušan Simić
