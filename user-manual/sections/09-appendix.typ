= Appendix

== Supported radios (complete list)

The model ID in the first column is what you pass to `-R` on the CLI
and what appears in the GUI's *Radio model* dropdown.

#table(
  columns: (auto, 1fr, auto),
  align: (left, left, center),
  table.header[*Model ID*][*Hardware*][*Registered*],
  [`uv5r`],    [Baofeng UV-5R, UV-5R Plus, UV-5RA], [✅],
  [`uv6r`],    [Baofeng UV-6R],                     [✅],
  [`uv82`],    [Baofeng UV-82],                     [✅],
  [`uv25`],    [Baofeng UV-25 / UV-17 Pro],         [✅],
  [`rt470`],   [Radtel RT-470],                     [✅],
  [`rt470x`],  [Radtel RT-470X],                    [✅],
  [`rt900bt`], [Radtel RT-900BT],                   [✅],
  [`uv9r`],    [Baofeng UV-9R — experimental],      [no],
  [`k5plus`],  [Baofeng K5 Plus — experimental],    [no],
)

*Registered* means the model is available out of the box in the CLI
`-R` choices and the GUI dropdown. Unregistered models require a
one-line source change (remove the leading hash on the
`@register_radio` decorator) and a rebuild.

== Glossary

=== CTCSS (Continuous Tone-Coded Squelch System)

A sub-audible tone transmitted alongside your voice. Receivers tuned
to the same CTCSS tone unmute; receivers without the tone stay
silent. Also called "PL tone" (Motorola trademark) or "privacy tone".
Not actually private — the tone is standard across all radios.

=== DCS / DTCS (Digital-Coded Squelch / Digital Tone Coded Squelch)

Digital equivalent of CTCSS. A repeating low-rate digital code
(00.06–40.06 kHz bitstream) gates the squelch. Same function, better
at rejecting false positives from random sub-audible hum.

- `rdcs_code` / `tdcs_code` — RX and TX codes. Usually set equal.
- `dcs_polarity` — `"NN"` (both normal), `"RR"` (both reversed), or
  mixed (`"NR"`, `"RN"`).

=== Duplex

How TX and RX frequencies relate.

- `""` — simplex, TX and RX on the same frequency.
- `"+"` — TX is RX + offset (repeater input is above repeater output).
- `"-"` — TX is RX − offset.

=== Offset

The frequency difference between RX and TX in duplex mode, in MHz in
CHIRP CSV, in Hz in Radijator JSON.

=== TX power levels

Radios expose a small set of discrete power levels (Low, Mid, High).
CHIRP represents them as `PowerLevel` objects specific to the driver;
Radijator's defaults pick the highest level the driver exposes unless
the source JSON overrides it.

=== NFM / FM

Channel bandwidth.

- `NFM` — narrow FM, 12.5 kHz channel spacing. The default, and what
  almost all modern Chinese handheld radios ship with.
- `FM` — wide FM, 25 kHz channel spacing. Legacy; may be required for
  older repeaters.

== License and credits

Radijator is distributed under the same terms as its upstream
dependencies. See `LICENSE` in the repository root.

Radijator relies entirely on the radio driver work done by the CHIRP
project (#link("https://chirpmyradio.com/")[chirpmyradio.com]) —
without CHIRP there would be no Radijator. Support them; contribute
back driver fixes when you find them.
