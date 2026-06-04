# Radijator

Flash inexpensive Chinese handheld radios — Baofeng UV-5R/UV-82/UV-25, Radtel RT-470/RT-900BT and friends — without wrestling CHIRP's GUI for every operator. Drop a memory JSON and a settings profile, hit a button (or run one command), and the radio is ready.

Built on the battle-tested [CHIRP](https://chirpmyradio.com/) driver suite — Radijator is a workflow layer, not a fork.

## What you get

- **GUI** (PySide6) — pick a model, pick a port, pick your files, click *Run*. Live progress bar driven by [Rich](https://github.com/Textualize/rich). Tabs for programming, converting, and DTMF-code logging.
- **CLI** — same operations, scriptable. Useful for batches and CI.
- **Per-radio DTMF tracking** — generate a sequential code for every flashed radio and append a `code,nickname` row to a CSV log. The UV-5R also gets its power-on message rewritten to match.
- **JSON → CHIRP CSV** — convert your memory files into CHIRP's import format.
- **Pre-built binaries** — every push to `main` produces standalone Linux and Windows binaries via GitHub Actions; no Python required for end users.

## Supported radios

| Model ID | Hardware |
|----------|----------|
| `uv5r` | Baofeng UV-5R, UV-5R Plus, UV-5RA |
| `uv6r` | Baofeng UV-6R |
| `uv82` | Baofeng UV-82 |
| `uv25` | Baofeng UV-25 / UV-17 Pro |
| `rt470` | Radtel RT-470 |
| `rt470x` | Radtel RT-470X |
| `rt900bt` | Radtel RT-900BT |

(UV-9R and K5 Plus drivers are present but not registered — see TODOs in [cli/drivers.py](cli/drivers.py).)

## Quick start (end users)

Grab the latest `radijator-linux.zip` or `radijator-windows.zip` from the [Actions](../../actions) tab on GitHub. Inside you'll find two executables:

- `radijator` / `radijator.exe` — the CLI.
- `radijator-gui` / `radijator-gui.exe` — the GUI.

On Linux, add yourself to the `dialout` group so you can talk to the USB-serial cable. The user manual ([user-manual/main.typ](user-manual/main.typ), built as a PDF in CI) walks through everything: install, GUI tour, CLI reference, file formats, troubleshooting.

## Development setup

A CHIRP checkout sits next to this repo and gets installed into the venv:

```sh
./download_dev_dependencies.sh    # sparse-clone of kk7ds/chirp into ./chirp/
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install ./chirp
pre-commit install                # black formatter on every commit
```

On Linux, comment out the `wxPython` line in `chirp/requirements.txt` before installing — Radijator doesn't use wxPython directly.

Run it:

```sh
python radijator.py --help        # CLI
python radijator_gui.py           # GUI
typst compile --root user-manual user-manual/main.typ    # user manual PDF
```

Architecture notes, gotchas (CHIRP's stdout hijack, DeprecationWarning ordering, …), and the recipe for adding a new radio live in [AGENTS.md](AGENTS.md).

## AI-assisted development

This project is developed with help from AI agents — [Claude Code](https://claude.com/claude-code) at the moment. The [AGENTS.md](AGENTS.md) file (which `CLAUDE.md` symlinks to) gives any fresh agent session the context it needs to be productive: repo layout, code style, architectural decisions, and the non-obvious gotchas. Human review still happens for every change.

## License

BSD 2-clause. See [LICENSE](LICENSE).

## Author

Dušan Simić
