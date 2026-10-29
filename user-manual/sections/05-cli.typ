= CLI reference

== Invocation and global flags

```
radijator [--version] [-h] {program,convert,random-dcs} ...
```

- `--version` — print version and exit.
- `-h`, `--help` — short usage summary. Works on every subcommand too
  (`radijator program -h`, `radijator program upload-memory -h`, ...).

== `program` subcommand

Reads from or writes to the radio. General shape:

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
    header is written automatically. Each successful run adds one
    row. Coupled with `--dtmf-code` and `--dtmf-nickname`.],
  [`--dtmf-real-name`],
    [Optional. Real name of the operator, written to the CSV only. It
    is not programmed onto the radio. Requires the three flags above.],
)

The DTMF flags apply only to the `upload-*` modes. With any other mode
the run stops with an error. The run also stops before it touches the
radio if the code is already in the CSV log, or if the CSV log has
malformed rows.

A combined example flashing memories and logging the DTMF code:

```sh
radijator program -R uv5r -p /dev/ttyUSB0 \
  --dtmf-code "*042#" --dtmf-nickname "alice" \
  --dtmf-real-name "Alice Petrović" --dtmf-csv dtmf.csv \
  upload-memory -M memories/pmr.json
```

The row `*042#,alice,Alice Petrović` is added to `dtmf.csv` only if
the flash succeeds.

=== Progress output

When stdout is attached to a terminal, `program` renders a live
display built on the #link("https://github.com/Textualize/rich")[Rich]
library:

- one *progress bar* per phase reported by the underlying CHIRP
  driver — byte-level download/upload counts, per-channel memory
  clear/write counts. Completed bars stay visible.
- a *spinner status line* above the bars for single-step phases that
  do not report numeric progress — e.g. "Applying settings
  profile...", "Wait 6 seconds for radio to reset...".
- timestamped log lines for each `Downloading…`, `Uploading…`,
  `Done.` message.

When stdout is piped or redirected, the live display is suppressed
and Radijator falls back to plain `print` for log lines (no progress
bar, no spinner), keeping scripted output clean.

=== Mode: `print-settings`

Reads the current settings from the radio and prints them to stdout.
Does not write.

```sh
radijator program -R uv5r -p /dev/ttyUSB0 print-settings
```

=== Mode: `download-profile`

Reads the settings from the radio and writes them to a profile JSON
file. Does not write to the radio.

```sh
radijator program -R uv5r -p /dev/ttyUSB0 download-profile \
  -P settings_profile.json -o my-uv5r.json
```

- `-P`, `--profile` — required, the master settings profile. It
  tells Radijator which settings to read. Only the settings that the
  master defines for this model are written.
- `-o`, `--output` — required, destination JSON path. Overwrites if
  it exists. It must not be the same file as `-P`: the output holds
  only this model's entries, so it would remove all other models from
  the master.

The output has the same shape as `settings_profile.json`, so you can
give it to `upload-profile` later. A setting that the radio reports
as out of range is not written; the log shows a line for each one.

=== Mode: `upload-profile`

Applies a settings profile JSON and writes the result back.

```sh
radijator program -R uv5r -p /dev/ttyUSB0 upload-profile \
  -P settings_profile.json
```

- `-P`, `--profile` — required, path to the settings profile JSON.

=== Mode: `download-memory`

Reads all non-empty channels from the radio and writes them to a
memory JSON file. Does not write to the radio.

```sh
radijator program -R uv5r -p /dev/ttyUSB0 download-memory \
  -o my-channels.json
```

- `-o`, `--output` — required, destination JSON path. Overwrites if
  it exists.

The output has the memory JSON shape, so you can give it to
`upload-memory` or `convert` later. The file does not contain the
power level: on upload, every channel gets the model's default power
level, the same as for a hand-written file.

=== Mode: `upload-memory`

Clears all memories on the radio and writes the channels from one or
more memory JSON files.

```sh
radijator program -R uv5r -p /dev/ttyUSB0 upload-memory \
  -M memories/pmr.json
```

- `-M`, `--memory` — required, path to a memory JSON file. Repeat the
  flag to concatenate multiple files in order:

```sh
radijator program -R rt470x -p /dev/ttyUSB0 upload-memory \
  -M memories/pmr.json \
  -M memories/repeaters.json
```

=== Mode: `upload-profile-and-memory`

Both `upload-profile` and `upload-memory` in a single pass (settings
first, then memories). Combines their flags:

```sh
radijator program -R uv5r -p /dev/ttyUSB0 upload-profile-and-memory \
  -P settings_profile.json \
  -M memories/pmr.json
```

=== Legacy mode names

Releases before 1.2.0 used `load-profile`, `load-memory` and
`load-profile-and-memory`. These names still work as aliases of the
matching `upload-*` modes.

== `convert` subcommand

Converts one or more Radijator memory JSON files into a single
CHIRP-compatible CSV. No radio involved.

```sh
radijator convert -M memories/pmr.json pmr.csv
radijator convert -M memories/pmr.json -M memories/repeaters.json all.csv
```

- `-M`, `--memory` — required, path to a memory JSON file. Repeat
  to concatenate multiple files in order; the resulting CSV
  numbers channels sequentially across the whole concatenation.
- *positional* `output` — destination CSV path. Overwrites if it
  exists.

*Breaking change*: previous releases used `-i/--input` and
`-o/--output`. The flag names mirror `program upload-memory -M` now
and the output is a positional argument. Migrate scripts
accordingly.

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
