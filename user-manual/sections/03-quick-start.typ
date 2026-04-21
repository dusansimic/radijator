= Quick start

Two common tasks, start to finish.

== Flash a UV-5R with the GUI

Goal: write a handful of PMR channels onto a freshly powered Baofeng
UV-5R.

1. Connect the programming cable to the radio. Turn the radio on. On
  Linux, check the cable shows up with `ls /dev/ttyUSB*`. On Windows,
  check Device Manager → Ports (COM & LPT) for the new `COMx`.
2. Launch `radijator-gui` (or `radijator-gui.exe`).
3. On the *Program* tab:
  - *Radio model:* `uv5r`
  - *Serial port:* `/dev/ttyUSB0` (Linux) or `COM3` (Windows) —
    hit *Refresh* if your port is not listed.
  - *Operation:* `Load memory`
4. In the *Memory files* group, click *Add...* and pick
  `memories/pmr.json` from the repository (or your own memory JSON).
5. Click *Run*.

You will see log lines scroll by — first the radio dumps its current
firmware, then Radijator clears the existing memories, writes the new
ones, and uploads everything back. The progress bar tracks the
per-channel writes. When finished, the log ends with `=== Done ===` and
the progress bar reads *Done*.

Power-cycle the radio and the new channels are in place.

== Convert a JSON memory file to CHIRP CSV

Useful when you want to open the memories in CHIRP itself, audit them in
a spreadsheet, or import them into another tool.

```sh
radijator convert -i memories/pmr.json -o pmr.csv
```

Output:

```
Converted 16 memories from memories/pmr.json to pmr.csv
```

`pmr.csv` is now a CHIRP-compatible CSV you can import via *File → Open*
in CHIRP or inspect with any spreadsheet.
