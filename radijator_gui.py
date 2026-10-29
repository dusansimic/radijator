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


def _icon_path():
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", "radijator.png")


def main():
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from gui.main_window import MainWindow

    if sys.platform == "win32":
        # Without an explicit AppUserModelID, Windows groups the window under
        # python.exe and shows its icon in the taskbar when run from source.
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("radijator.gui")

    app = QApplication(sys.argv)
    app.setApplicationName("Radijator")
    app.setWindowIcon(QIcon(_icon_path()))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException as e:
        _log_crash(e)
        raise
