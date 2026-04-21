= Radio-specific notes

== Serial port naming

=== Windows

Ports show up as `COM3`, `COM4`, etc. Find the right one in *Device
Manager* → *Ports (COM & LPT)*. When you plug the cable in, a new
entry appears; that is your port.

Most Baofeng / Radtel cables use either a Prolific PL-2303 or a
CH340 / CH341 USB-serial chip. Driver downloads from the manufacturer
are sometimes required on fresh Windows installs — without the driver
the cable shows up as an unknown device.

=== Linux

Ports show up as `/dev/ttyUSB0`, `/dev/ttyUSB1`, etc. The kernel
usually autoloads `ch341` or `pl2303`. Confirm with `dmesg | tail`
after plugging in:

```
usb 1-2: ch341-uart converter now attached to ttyUSB0
```

If you have multiple USB-serial devices attached, the numbering
depends on plug order. When in doubt, unplug everything else, then
just the radio cable.

== Entering programming mode

Most of the supported radios do *not* need an explicit programming
mode — Radijator sends the vendor-specific handshake that the CHIRP
driver expects over the running radio. A few caveats:

- *Turn the radio on* before starting a run. Radios powered off during
  `download_fw` time out or report garbled responses.
- *Set volume to mid-range*. Some UV-5R variants are picky about audio
  levels on the mic/SP line that carries the serial data.
- *Use a fresh battery* — programming takes 30–90 s depending on the
  model; a brown-out mid-upload can leave the radio in an
  inconsistent state that requires a factory reset.

== Per-driver caveats

=== Baofeng UV-5R and UV-82

Rock-solid. The UV-5R family is what Radijator was built against. A
reset wait of 6 s between download and upload is baked into the
driver class; this matches the BL-5 bootloader timing.

=== Baofeng UV-6R

Works with the same handshake as the UV-5R. Driver is registered but
not covered by the default `settings_profile.json`; contribute a
`uv6r` branch to the profile JSON if you need settings-profile
support.

=== Baofeng UV-9R

*Experimental.* The driver class exists but is not registered by
default; enabling it requires a code change. The CHIRP driver for the
WP970i family is known to be flaky on some UV-9R firmware revisions.

=== Baofeng UV-25 / UV-17 Pro

Registered as `uv25`. The same driver family also covers the K5 Plus
under the model ID `k5plus`, but K5 Plus is not registered by default
because of a CHIRP-side logging exception that has not yet been
resolved.

=== Radtel RT-470 and RT-470X

Two separate driver classes (`rt470` and `rt470x`) because the models
differ enough internally. Pick the one that matches your hardware;
getting this wrong typically results in a garbled radio image that
has to be factory-reset.

=== Radtel RT-900BT

Registered as `rt900bt`. Same CHIRP-side logging issue as the K5 Plus
can surface in verbose mode — turn `--verbose` off if you hit
tracebacks mid-run.
