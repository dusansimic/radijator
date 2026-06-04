#!/usr/bin/env python3
"""Radijator entry script. Domain code lives in the cli/ package.

This module also re-exports the symbols the PySide6 GUI references via
`import radijator`, so gui/*.py needs no edits after the split.
"""

# chirp.wxui.serialtrace hijacks sys.stdout/sys.stderr at import time,
# routing them into ~/.chirp/debug.log. Save and restore around the import.
import sys as _sys
_saved_stdout, _saved_stderr = _sys.stdout, _sys.stderr
from chirp.wxui.serialtrace import SerialTrace  # noqa: F401
_sys.stdout, _sys.stderr = _saved_stdout, _saved_stderr
del _sys, _saved_stdout, _saved_stderr

__version__ = "1.0.0"

# Importing cli.drivers populates RADIO_MODEL_ID_CLASS_DICT via the
# @register_radio decorator side effect; do this before exposing the dict.
from cli import drivers as _drivers  # noqa: F401
from cli.convert import run_convert  # noqa: F401
from cli.dtmf import DTMF_CODE_RE, _next_dtmf_code  # noqa: F401
from cli.main import _log_crash, main
from cli.memory import RadijatorMemory  # noqa: F401
from cli.program import run_program  # noqa: F401
from cli.radio import RADIO_MODEL_ID_CLASS_DICT  # noqa: F401


if __name__ == "__main__":
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException as e:
        _log_crash(e, "radijator")
        raise
