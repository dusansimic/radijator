#!/usr/bin/env python3
import os
import sys
import tempfile
import traceback


def _log_crash(exc):
    path = os.path.join(tempfile.gettempdir(), "radijator-gui-crash.log")
    try:
        with open(path, "w") as f:
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
        sys.stderr.write(f"Crash log written to {path}\n")
    except Exception:
        traceback.print_exc()


def main():
    from PySide6.QtWidgets import QApplication

    from gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Radijator")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        _log_crash(e)
        raise
