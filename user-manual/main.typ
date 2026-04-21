#set document(title: "Radijator User Manual", author: "Radijator")
#set page(paper: "a4", margin: 2cm, numbering: "1")
#set text(size: 11pt, font: "New Computer Modern")
#set heading(numbering: "1.1")
#show link: set text(fill: blue.darken(20%))
#show raw.where(block: false): box.with(
  fill: luma(240),
  inset: (x: 3pt, y: 0pt),
  outset: (y: 3pt),
  radius: 2pt,
)
#show raw.where(block: true): block.with(
  fill: luma(245),
  inset: 8pt,
  radius: 3pt,
  width: 100%,
)

#align(center)[
  #text(size: 26pt, weight: "bold")[Radijator User Manual]

  #v(0.4em)
  #text(size: 13pt)[Flashing Chinese radios without the pain]

  #v(2em)
  #text(size: 10pt)[Version 1.0.0]
]

#v(3em)

#outline(title: "Table of contents", depth: 2)

#pagebreak()

#include "sections/01-introduction.typ"
#pagebreak()
#include "sections/02-installation.typ"
#pagebreak()
#include "sections/03-quick-start.typ"
#pagebreak()
#include "sections/04-gui.typ"
#pagebreak()
#include "sections/05-cli.typ"
#pagebreak()
#include "sections/06-file-formats.typ"
#pagebreak()
#include "sections/07-radio-notes.typ"
#pagebreak()
#include "sections/08-troubleshooting.typ"
#pagebreak()
#include "sections/09-appendix.typ"
