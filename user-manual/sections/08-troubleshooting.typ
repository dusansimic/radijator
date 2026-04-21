= Troubleshooting

== Crash log locations

When Radijator hits an unhandled exception, it writes the full Python
traceback to a crash log on disk before re-raising. This exists
because packaged binaries on Windows sometimes swallow stderr,
leaving users with only `Failed to execute script` and no detail.

- Linux / macOS:
  - CLI: `/tmp/radijator-crash.log`
  - GUI: `/tmp/radijator-gui-crash.log`
- Windows: same file names, under `%TEMP%` (typically
  `C:\Users\<you>\AppData\Local\Temp\`).

The log is overwritten on each crash. Attach it to bug reports.

Note that successful runs do *not* write a crash log. `--help` and
`--version` also do not — normal exits via `SystemExit` are
deliberately not treated as crashes.

== Common failures

=== `Permission denied: '/dev/ttyUSB0'`

Your user is not in the serial group. See *Installation → Linux
serial port access*. After adding yourself to `dialout` / `uucp`, log
out and back in.

=== `FileNotFoundError: [Errno 2] ... /dev/ttyUSB0`

Cable not plugged in, or the port name is wrong. Re-check with
`ls /dev/ttyUSB*` (Linux) or Device Manager (Windows). Use the GUI's
*Refresh* button after plugging in.

=== Wrong radio model — upload succeeds but radio is bricked-ish

Symptom: the radio powers on but settings look wrong, channels missing
or garbled. Cause: the `-R` model ID did not match the actual
hardware, so Radijator wrote a valid-but-wrong memory layout.

Fix: factory-reset the radio (hold Menu + power on, or the
model-specific reset combo), then re-run with the correct `-R` /
model dropdown selection.

=== Radio times out during download

Symptom: the run hangs on "Downloading settings from radio..." and
eventually errors out.

Possible causes:

- Radio is off, or powered off mid-handshake.
- Cable is flaky — try another USB port, or a known-good cable.
- The CH340 / PL2303 driver on Windows is stale. Reinstall from the
  vendor.
- The radio is in an odd firmware mode (e.g. FM radio on, squelch
  screen open). Return to the normal channel display before starting.

=== Profile contains a setting the driver doesn't expose

Radijator silently skips settings whose name does not match any node
in the driver's settings tree. If you expected a setting to be
written and it wasn't, run
`radijator program -R <model> print-settings` and check the exact
name the driver reports.

== Filing a bug report

Include:

1. Radijator version (`radijator --version`, or Help → About in the
  GUI).
2. Platform (Linux distro + kernel, or Windows build).
3. Radio model and firmware version (usually printed at the top of
  `print-settings` output).
4. The exact command (for CLI) or the fields you filled in (for GUI).
5. The contents of the crash log if applicable.
6. Relevant memory / profile JSON files, minimised to the smallest
  reproducer.

Open the issue on the Radijator GitHub repository.
