#import "../common.typ": screenshot

= GUI reference

== Launching the GUI

From a prebuilt binary:

```sh
./radijator-gui        # Linux
radijator-gui.exe      # Windows
```

From source:

```sh
python radijator_gui.py
```

The window title shows the running version, e.g. `Radijator 1.0.0`.

== Main window layout

#screenshot(
  "/assets/main-window.png",
  [The main window on first launch.],
)

The window is split vertically. The top pane holds the two action tabs,
*Program* and *Convert*. The bottom pane holds:

- a *log console* — read-only, append-only, auto-scrolls as a run
  proceeds. Keeps up to 5000 lines; older output falls off the top.
- a *progress bar* — shows the current step and total (e.g. "Writing
  memories (42/128)") during a run, and settles on *Done* or *Failed*
  at the end.

The divider between the tabs and the log can be dragged to give either
pane more room.

=== Menus

- *File → Quit* — closes the window.
- *Help → About* — version, short description, attribution.

== Program tab

#screenshot(
  "/assets/program-tab-load-profile-and-memory.png",
  [Program tab configured for a
    #raw("load-profile-and-memory") run: model, port, operation,
    profile, and two memory files queued in order.],
)

All radio-writing operations live here. The fields, top to bottom:

=== Radio model

Dropdown populated from the driver registry. Pick the model ID that
matches your hardware (e.g. `uv5r`, `rt470x`). See the appendix for
the full list and the quirks per family.

=== Serial port + Refresh

Dropdown of auto-detected ports. The field is editable — if your OS
names ports in a way Radijator does not recognise, type the path
directly. *Refresh* re-scans after you plug a cable in.

- Linux: `/dev/ttyUSB0`, `/dev/ttyUSB1`, ...
- Windows: `COM3`, `COM4`, ...

=== Operation

Four modes. Radijator enables only the input groups relevant to each:

#table(
  columns: (auto, 1fr),
  align: (left, left),
  table.header[*Mode*][*What it does*],
  [*Print settings*],
    [Read current settings from the radio and print them to the log.
    No write. Good first step to confirm the cable and model selection
    work.],
  [*Load profile*],
    [Read current state, apply the named settings from a *settings
    profile JSON*, and write back.],
  [*Load memory*],
    [Read current state, clear all memory channels, write the channels
    from one or more *memory JSON* files, and write back.],
  [*Load profile and memory*],
    [Both of the above in one pass — settings first, then memories.],
)

=== Verbose

When enabled, the log shows every individual setting being written and
every memory channel line — useful when debugging a bad profile or
memory file. Off by default; the normal log is already detailed enough
for routine runs.

=== Settings profile

Enabled only in *Load profile* and *Load profile and memory* modes.
Type a path or use *Browse...* to pick a JSON file. See the
*File formats* section for the schema.

=== Memory files

Enabled only in *Load memory* and *Load profile and memory* modes.

- *Add...* — opens a multi-select file dialog. Selected files are
  appended to the list.
- *Remove* — deletes the highlighted entries from the list.
- *Order matters*: files are concatenated in list order. The first
  file's first memory goes into channel 1, and so on. If you add the
  same file twice, its memories appear twice.

=== Run

Executes the current operation. Disabled during a run. A dialog pops
up if required inputs are missing (e.g. a memory file for *Load
memory* mode).

== Convert tab

#screenshot(
  "/assets/convert-tab.png",
  [Convert tab with input JSON and output CSV paths set.],
)

Converts a Radijator memory JSON into a CHIRP-compatible CSV.

- *Input JSON* — the source memory file.
- *Output CSV* — where to write the result. Overwrites any existing
  file.
- *Convert* — runs the conversion. A single log line reports how many
  memories were converted.

No serial port, no radio needed — this is a pure file transform.

== Interpreting log output and progress

#screenshot(
  "/assets/run-in-progress.png",
  [A run underway: log streaming, progress bar tracking the current
    phase.],
)

A typical `load-profile-and-memory` run looks like this:

```
Downloading settings from radio...
Wait 6 seconds for radio to reset...
Applying settings profile...
Clearing existing memories...
Setting new memories...
Uploading to radio...
Done.

=== Finished ===
```

Progress bar states:

- *Idle* — nothing running.
- *Running...* — operation started, step count not yet known
  (indeterminate animation).
- *Downloading from radio* — reading radio contents.
- *Writing memories (n/total)* — per-channel counter during the write
  loop. This is the longest phase on most radios.
- *Uploading to radio* — sending the modified image back.
- *Done* — success (bar full, green on most themes).
- *Failed* — an exception was raised; the full traceback is in the log.

If a run fails, the tabs unlock automatically so you can fix inputs and
retry without restarting the GUI.
