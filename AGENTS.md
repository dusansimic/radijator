# Radijator — agent guide

A workflow tool for flashing Baofeng / Radtel handheld radios via CHIRP drivers. Ships a CLI and a PySide6 GUI from the same Python code, plus a Typst user manual. End users get pre-built Linux/Windows binaries from CI.

## Repo layout

```
.
├─ radijator.py            # CLI entry script — thin shim, re-exports for GUI
├─ radijator_gui.py        # GUI entry script — launches PySide6 MainWindow
├─ cli/                    # All domain + CLI logic (see "Architecture")
│  ├─ memory.py            # RadijatorMemory data class
│  ├─ radio.py             # RadijatorRadio base + register_radio + registry
│  ├─ drivers.py           # Concrete driver subclasses (UV-5R, RT-470, …)
│  ├─ dtmf.py              # DTMF helpers (regex, CSV append, next code)
│  ├─ program.py           # run_program() — download → mutate → upload
│  ├─ convert.py           # run_convert() — JSON memory → CHIRP CSV
│  ├─ random_dcs.py        # random-dcs helper
│  ├─ progress.py          # Rich Live + Progress + Status reporter
│  └─ main.py              # argparse, dispatch, crash log
├─ gui/                    # PySide6 widgets
│  ├─ main_window.py       # QMainWindow + tabs + menu
│  ├─ program_tab.py       # Program inputs (radio, port, mode, …)
│  ├─ convert_tab.py       # JSON → CSV converter UI
│  ├─ dtmf_tab.py          # DTMF CSV log viewer
│  └─ worker.py            # QThread wrapping run_program/run_convert
├─ user-manual/            # Typst user manual sources (compiles to PDF)
├─ memories/               # Sample memory JSON files
├─ settings_profile.json   # Per-radio human-readable setting → CHIRP path map
├─ deprecated/             # Legacy stand-alone scripts; do NOT touch
├─ chirp/                  # kk7ds/chirp checkout — .gitignored, not ours
├─ radijator.spec          # PyInstaller spec: builds both binaries
├─ pyproject.toml          # Black config
├─ .pre-commit-config.yaml # Black hook
└─ requirements*.txt       # Runtime + dev deps
```

## Setup

CHIRP is required but not vendored. Use the helper:

```sh
./download_dev_dependencies.sh    # sparse-clones kk7ds/chirp into ./chirp/
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install ./chirp               # installs CHIRP into the venv
pre-commit install                # one-time, wires the black hook
```

On Linux, CHIRP's `requirements.txt` lists `wxPython`; comment it out before installing CHIRP's deps (the system `python3-wxpython4` package suffices, and Radijator doesn't use wxPython directly).

## Running locally

```sh
python radijator.py --help
python radijator.py convert -i memories/pmr.json -o /tmp/pmr.csv
python radijator.py program -R uv5r -p /dev/ttyUSB0 print-settings
python radijator_gui.py
```

## Code style

- **Black** enforces formatting (line 88, target py312). `pre-commit` runs it on every staged Python file. `deprecated/` is excluded.
- **Conventional Commits** for messages. The `caveman:caveman-commit` skill is the project's go-to commit-message generator — ultra-terse, no AI attribution, body only when "why" isn't obvious.
- **No comments unless WHY is non-obvious.** Don't restate what well-named code already says.
- **No emojis in code, docs, or commits.**
- **Don't touch `deprecated/` or `chirp/`.** First is legacy reference; second is upstream.

## Architecture

### Two entry scripts, one domain

`radijator.py` and `radijator_gui.py` are entry scripts. All domain logic lives in `cli/`. `radijator.py` does three jobs:

1. Runs the `chirp.wxui.serialtrace` `stdout/stderr` prelude (see Gotchas).
2. Re-exports the symbols `gui/*.py` references via `import radijator` — `__version__`, `RADIO_MODEL_ID_CLASS_DICT`, `RadijatorMemory`, `DTMF_CODE_RE`, `_next_dtmf_code`, `run_program`, `run_convert`. These are intentional re-exports — leave the `# noqa: F401` tags.
3. Dispatches `main()` under `__name__ == "__main__"`.

The GUI does NOT import from `cli.*` directly; it goes through `radijator`. This is intentional — it keeps the GUI insulated from the package split.

### Driver registry pattern

Each concrete radio is a subclass of `RadijatorRadio` decorated with `@register_radio`. Importing `cli.drivers` populates `cli.radio.RADIO_MODEL_ID_CLASS_DICT` as a side effect. Both `radijator.py` and `cli/main.py` import `cli.drivers` *before* reading the registry, so the side-effect ordering matters.

### `progress_fn` / `log_fn` injection

`run_program()` accepts `log_fn` and `progress_fn` callables. CHIRP's `radio.status_fn` is bridged onto `progress_fn` in `RadijatorRadio.download_fw` / `upload_fw`. The CLI wires Rich's `Live` (`cli/progress.py: cli_reporter()`) to those callables; the GUI wires Qt signals from `gui/worker.py`. Same domain code, two front-ends.

### Settings-profile semantics

`settings_profile.json` maps a *human-readable* setting name → per-model `{name: CHIRP setting path, value: …}`. `RadijatorRadio._transpose_settings_profile` filters to the active `RADIJATOR_SETTINGS_PROFILE_ID` and applies the values during `set_settings_profile`. GUI / CLI can override individual values via the `profile_overrides` dict (used by the DTMF feature to override power-on message).

## Gotchas

- **`chirp.wxui.serialtrace` hijacks stdout/stderr** at import time, routing them into `~/.chirp/debug.log`. The prelude in `radijator.py` saves and restores `sys.stdout` / `sys.stderr` around the import. Do not move this block — it must run before any chirp driver code touches stdio.
- **`chirp.drivers/__init__.py` prepends a `("once", DeprecationWarning, "chirp.drivers")` filter** to silence its non-byte-native get_raw/set_raw warnings. We add a `("ignore", DeprecationWarning, r"chirp\..*")` filter *after* importing `cli.drivers`, so ours ends up at the front of the chain. If you move the filter line up, the warnings leak through `logging.captureWarnings(True)` (also set by chirp.wxui) and clobber the Rich Live display.
- **`SerialTrace` is wxPython-adjacent**, but the actual `chirp.wxui.serialtrace` module avoids importing wx (it's stripped from CHIRP's requirements on Linux). It's safe to import without wxPython installed.
- **PyInstaller spec** ([radijator.spec](radijator.spec)) uses `collect_submodules('chirp')` filtered to exclude `chirp.wxui.*` except `serialtrace`. Don't loosen the filter — CHIRP's wxui modules can't import without wxPython and PyInstaller will spam error lines.

## Adding a radio

1. Find the CHIRP driver class for the model (under `chirp/drivers/`).
2. Add a subclass in `cli/drivers.py`:
   ```python
   @register_radio
   class RadijatorFOO(RadijatorRadio):
       DRIVER_CLASS = FooRadio
       RADIJATOR_SETTINGS_PROFILE_ID = "foo"
       RESET_TIME = 5  # seconds; check the driver's clone timing
   ```
3. Add per-model entries to `settings_profile.json` under the `RADIJATOR_SETTINGS_PROFILE_ID` you chose.
4. If the radio needs custom DTMF / power-on-message / memory-extras handling, override `set_dtmf_code`, `set_power_on_message`, `_apply_memory_extras`. The UV-5R class in `cli/drivers.py` is the worked example.
5. Document the model in `user-manual/sections/07-radio-notes.typ`.

## Build & CI

- `radijator.spec` builds two binaries: `radijator` (console) and `radijator-gui` (windowed). `pyinstaller radijator.spec` on Linux or Windows.
- `.github/workflows/build.yml` matrix-builds for Linux + Windows on every push to `main`. Artifacts retained for 1 day.
- `.github/workflows/user-manual.yml` compiles the Typst manual on changes to `user-manual/` and uploads the PDF.
- Screenshots in `user-manual/assets/*.png` are tracked via Git LFS — `git lfs install` once per clone.

## User manual

Typst sources under `user-manual/`. Build locally:

```sh
typst compile --root user-manual user-manual/main.typ
```

The `--root user-manual` flag is required because section files reference `/assets/...` rooted at the manual directory.

## Memory system

Long-term project context lives under `~/.claude/projects/.../memory/`. The auto-memory layer is set up; consult it for prior session decisions and user preferences before assuming anything.

## What this project is NOT

- Not a CHIRP fork. We wrap CHIRP drivers; never modify `chirp/`.
- Not a general-purpose radio programmer. Scope is fixed: Baofeng / Radtel families used by the operator.
- Not a CHIRP CSV editor. `convert` is one-way (JSON → CHIRP CSV); no round-trip.
