= CLI reference

== Invocation and global flags

```
radijator [--version] [-h] {program,convert,random-dcs} ...
```

- `--version` — print version and exit.
- `-h`, `--help` — short usage summary. Works on every subcommand too
  (`radijator program -h`, `radijator program load-memory -h`, ...).

== `program` subcommand

Writes to the radio. General shape:

```
radijator program -R <model> -p <port> [--verbose] <mode> [mode-args]
```

=== Flags

#table(
  columns: (auto, 1fr),
  align: (left, left),
  table.header[*Flag*][*Meaning*],
  [`-R`, `--radio-model`],
    [Required. Model ID (see appendix). Examples: `uv5r`, `rt470x`.],
  [`-p`, `--port`],
    [Serial port. Defaults to `/dev/ttyUSB0`. On Windows supply the
    `COMx` name.],
  [`--verbose`],
    [Log every individual setting write or memory line. Off by default.],
  [`--dtmf-code`],
    [DTMF code for this radio. Must match `*ddd#` (asterisk, three
    digits, hash). Coupled with `--dtmf-nickname` and `--dtmf-csv` —
    pass all three or none.],
  [`--dtmf-nickname`],
    [Human-readable label written alongside the DTMF code. Coupled
    with `--dtmf-code` and `--dtmf-csv`.],
  [`--dtmf-csv`],
    [Path to the DTMF log CSV. Created on first use; the
    `code,nickname` header is written automatically. Subsequent runs
    append one row each. Coupled with `--dtmf-code` and
    `--dtmf-nickname`.],
)

A combined example flashing memories and logging the DTMF code:

```sh
radijator program -R uv5r -p /dev/ttyUSB0 \
  --dtmf-code "*042#" --dtmf-nickname "alice" \
  --dtmf-csv dtmf.csv \
  load-memory -M memories/pmr.json
```

The row `*042#,alice` is appended to `dtmf.csv` only if the flash
succeeds.

=== Mode: `print-settings`

Reads the current settings from the radio and prints them to stdout.
Does not write.

```sh
radijator program -R uv5r -p /dev/ttyUSB0 print-settings
```

=== Mode: `load-profile`

Applies a settings profile JSON and writes the result back.

```sh
radijator program -R uv5r -p /dev/ttyUSB0 load-profile \
  -P settings_profile.json
```

- `-P`, `--profile` — required, path to the settings profile JSON.

=== Mode: `load-memory`

Clears all memories on the radio and writes the channels from one or
more memory JSON files.

```sh
radijator program -R uv5r -p /dev/ttyUSB0 load-memory \
  -M memories/pmr.json
```

- `-M`, `--memory` — required, path to a memory JSON file. Repeat the
  flag to concatenate multiple files in order:

```sh
radijator program -R rt470x -p /dev/ttyUSB0 load-memory \
  -M memories/pmr.json \
  -M memories/repeaters.json
```

=== Mode: `load-profile-and-memory`

Both `load-profile` and `load-memory` in a single pass (settings
first, then memories). Combines their flags:

```sh
radijator program -R uv5r -p /dev/ttyUSB0 load-profile-and-memory \
  -P settings_profile.json \
  -M memories/pmr.json
```

== `convert` subcommand

Converts a Radijator memory JSON into a CHIRP-compatible CSV. No radio
involved.

```sh
radijator convert -i memories/pmr.json -o pmr.csv
```

- `-i`, `--input` — required, source JSON.
- `-o`, `--output` — required, destination CSV (overwrites).

== `random-dcs` subcommand

Assigns a random DCS code and polarity (`NN` or `RR`) to every memory
in the input file and writes the result to a new JSON file. Useful for
seeding pre-shared squelch codes on a fleet of radios.

```sh
radijator random-dcs -i memories/pmr.json -o memories/pmr-dcs.json
```

- `-i`, `--input` — required, source JSON.
- `-o`, `--output` — required, destination JSON.

Re-running the command re-randomises. The DCS tone mode is set to
`DTCS`, the same code is assigned to both TX and RX, and the polarity
is picked from `["NN", "RR"]`.

This subcommand is intentionally absent from the GUI — it is a
generator, not a flashing workflow, and composes better as a shell
command.

== Exit codes

- `0` — success.
- `2` — argparse error (unknown flag, missing required argument).
- non-zero — uncaught exception during the run. A full traceback is
  written to a crash log (see *Troubleshooting*) and the same
  exception is re-raised, so the shell sees a non-zero exit.
