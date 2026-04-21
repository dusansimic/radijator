= File formats

All inputs are plain JSON. All outputs (except CHIRP CSV) are plain
JSON. No binary formats, no checksums — easy to diff, easy to keep in
git, easy to generate from scripts.

== Memory JSON

A memory JSON file is a *top-level array* of memory objects. Each
object describes one channel.

=== Fields

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  table.header[*Field*][*Type*][*Meaning*],
  [`name`], [string], [Display name on the radio. Usually 6–8 chars.],
  [`frequency`], [integer], [RX frequency in Hz. `446006250` = 446.00625 MHz.],
  [`number`], [integer], [Channel slot. Optional — Radijator auto-assigns
    1-based slots in array order if omitted.],
  [`tone`], [string], [Squelch tone mode. `""` = no tone, `"DTCS"` =
    digital code squelch.],
  [`rdcs_code`], [integer], [RX DCS code. Default `23`.],
  [`tdcs_code`], [integer], [TX DCS code. Default `23`.],
  [`dcs_polarity`], [string], [`"NN"`, `"NR"`, `"RN"` or `"RR"`.
    Default `"NN"`.],
  [`mode`], [string], [`"NFM"` (narrow FM) or `"FM"`. Default `"NFM"`.],
  [`tuning_step`], [number], [kHz. Default `5.0`.],
  [`duplex`], [string], [`""`, `"+"` or `"-"` (convert only).],
  [`offset`], [integer], [Repeater offset in Hz (convert only).],
)

Everything except `name` and `frequency` is optional; Radijator falls
back to the defaults shown above.

=== Example

```json
[
  {
    "name": "PMR 1",
    "frequency": 446006250
  },
  {
    "name": "PMR 2",
    "frequency": 446018750
  }
]
```

A richer example with DCS squelch:

```json
[
  {
    "name": "GROUP A",
    "frequency": 446050000,
    "tone": "DTCS",
    "rdcs_code": 155,
    "tdcs_code": 155,
    "dcs_polarity": "NN"
  }
]
```

== Settings profile JSON

A settings profile describes per-model radio settings by
*human-readable name*. Radijator looks up the CHIRP-specific setting
path for the active radio model and writes the matching value.

=== Structure

Top-level: an object keyed by human-readable setting name. Each value
is an object keyed by *radio model ID* (`uv5r`, `uv25`, `rt470`, ...).
Each per-model entry supplies the CHIRP setting path and the value to
write:

```json
{
  "Squelch Level": {
    "uv5r": { "name": "squelch",          "value": 1 },
    "uv25": { "name": "settings.squelch", "value": 1 },
    "rt470": { "name": "sql",             "value": 1 },
    "rt470x": { "name": "sql",            "value": 1 }
  },
  "Power Save": {
    "uv5r": { "name": "save",              "value": "1:4" },
    "uv25": { "name": "settings.savemode", "value": "On" },
    "rt470": { "name": "save",             "value": "Deep" },
    "rt470x": { "name": "save",            "value": "Deep" }
  }
}
```

When you run Radijator with `-R uv5r`, it iterates every setting path
known to the UV-5R driver; for each one that appears in the profile
under `uv5r`, it writes the value. Entries for models other than the
selected one are ignored.

If a setting exists in the profile but not for the selected model (no
`uv82` entry in the snippet above, for example), that setting is
silently skipped — profiles can safely be supersets.

=== How Radijator resolves paths

Internally, Radijator calls the CHIRP driver's `get_settings()`, walks
the resulting tree with `settings.walk()`, and for each node whose
name matches a profile entry, calls `setting[0] = value`. So `name`
must be the exact leaf name CHIRP reports — `squelch`, not
`Squelch Level`. Run `radijator program -R <model> print-settings` to
discover the exact names and their current values.

== CHIRP CSV output

The `convert` subcommand emits a CSV with the column set CHIRP's
`File → Open` expects. One row per memory, in array order.

#table(
  columns: (auto, 1fr),
  align: (left, left),
  table.header[*Column*][*Notes*],
  [`Location`], [1-based channel slot.],
  [`Name`], [From `name`, empty string if missing.],
  [`Frequency`], [MHz, derived from `frequency` Hz / 1e6.],
  [`Duplex`], [From `duplex` or `""`.],
  [`Offset`], [MHz, from `offset` Hz / 1e6, default 5.0.],
  [`Tone`], [From `tone` or `""`.],
  [`rToneFreq`, `cToneFreq`], [CTCSS tone frequencies, default 88.5.],
  [`DtcsCode`, `RxDtcsCode`], [From `tdcs_code` / `rdcs_code`, default "023".],
  [`DtcsPolarity`], [From `dcs_polarity`, default `"NN"`.],
  [`CrossMode`], [Defaults to `"Tone->Tone"`.],
  [`Mode`], [From `mode`, default `"NFM"`.],
  [`TStep`], [From `tstep`, default `"5.0"`.],
  [`Skip`], [From `skip`, default `""`.],
  [`Power`], [From `power`, default `"50W"`.],
  [`Comment`], [From `comment`, default `""`.],
  [`URCALL`, `RPT1CALL`, `RPT2CALL`, `DVCODE`],
    [D-STAR fields; defaults to `""`.],
)

Any of these columns can be populated from the source JSON by adding a
field with the lowercase CHIRP name (`duplex`, `cross_mode`, `power`,
`comment`, ...). Otherwise the defaults above are used.
