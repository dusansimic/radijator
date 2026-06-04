"""Terminal progress bar for CLI runs."""

import sys


def _make_cli_progress():
    """Return a progress_fn that draws a single-line bar on the TTY.

    Each new label starts a fresh line; lines complete with a newline
    when cur reaches total. When stdout is not a TTY (piped/redirected),
    the callable is a no-op so logs stay clean.
    """
    state = {"label": None}

    def progress(cur, total, label):
        if not sys.stdout.isatty():
            return
        if label != state["label"]:
            if state["label"] is not None:
                sys.stdout.write("\n")
            state["label"] = label
        width = 30
        pct = (cur / total) if total else 0.0
        filled = int(pct * width)
        bar = "#" * filled + "-" * (width - filled)
        sys.stdout.write(f"\r{label}: [{bar}] {cur}/{total}")
        sys.stdout.flush()
        if total and cur >= total:
            sys.stdout.write("\n")
            state["label"] = None

    return progress
