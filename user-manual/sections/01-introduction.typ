= Introduction

== What Radijator is

Radijator is a small tool that writes frequency memories and configuration
settings onto inexpensive Chinese handheld radios — Baofeng UV-5R, UV-82,
UV-25 and friends, plus several Radtel models — over a USB programming
cable.

It ships two front-ends built on the same programming engine:

- a *graphical interface* for point-and-click flashing, and
- a *command-line interface* for scripting and batch use.

Both read the same plain-text JSON files for memory channels and settings,
so profiles can be kept under version control and shared between users.

== Relationship to CHIRP

Radijator does not talk to radios directly. It wraps the battle-tested
radio drivers from
#link("https://chirpmyradio.com/")[CHIRP], a free
software radio programming suite, and adds a thin workflow layer on top:

- a small JSON schema for memory files,
- a "settings profile" concept that maps human-readable setting names to
  the per-model CHIRP setting paths,
- a progress-reporting loop tailored for slow serial transfers.

If a radio is supported by CHIRP and included in Radijator's driver list,
Radijator can program it.

== GUI vs CLI — when to use which

#table(
  columns: (auto, 1fr, 1fr),
  align: (left, left, left),
  table.header[*Use case*][*GUI*][*CLI*],
  [One-off flashing], [✅ easiest], [works, more typing],
  [Batch / scripted flashing], [no], [✅],
  [CI pipelines, reproducible builds], [no], [✅],
  [Inspecting current radio settings], [✅], [✅ (stdout)],
  [Converting JSON → CHIRP CSV], [✅], [✅],
  [Generating randomised DCS codes], [no], [✅ only],
  [Non-technical end users], [✅], [no],
)

The `random-dcs` helper is deliberately CLI-only; it is a generator, not
a workflow, and lives in scripts more comfortably than in a button.

== Supported radio models

Radijator currently ships drivers for the families listed below. See the
appendix for the full table including the exact model ID strings used
with `-R` on the CLI and in the GUI dropdown.

- Baofeng UV-5R / UV-5R Plus / UV-5RA
- Baofeng UV-82
- Baofeng UV-6R
- Baofeng UV-25 (UV-17 Pro)
- Radtel RT-470
- Radtel RT-470X
- Radtel RT-900BT
