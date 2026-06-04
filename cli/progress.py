"""Rich-based terminal reporter for CLI runs.

`cli_reporter()` is a context manager yielding `(log_fn, progress_fn)`
bound to a `rich.live.Live` display. On a TTY it renders:

- per-phase `rich.progress.Progress` bars for cur/max callbacks emitted
  by CHIRP drivers and the memory clear/write loops,
- a `rich.status.Status` spinner above the bars for single-step phases
  announced via `log_fn` messages ending in `...` (e.g. "Applying
  settings profile..."), so the user sees something animated even while
  no numeric progress is available.

When stdout is not a TTY (piped or redirected), the reporter degrades
to plain `print` for `log_fn` and a no-op `progress_fn`, keeping
scripted output clean.
"""

import sys
from contextlib import contextmanager

from rich.console import Console, Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.status import Status


class _CliDisplay:
    """Composable renderable that holds a Progress widget and a Status
    spinner, showing the status only when it has a message."""

    def __init__(self):
        self._console = Console()
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self._console,
            transient=False,
        )
        self._status = Status("", console=self._console)
        self._tasks = {}
        self._status_active = False

    @property
    def console(self) -> Console:
        return self._console

    def __rich__(self):
        if self._status_active:
            return Group(self._status, self._progress)
        return self._progress

    def update_progress(self, cur, total, label):
        task_id = self._tasks.get(label)
        if task_id is None:
            task_id = self._progress.add_task(label, total=total)
            self._tasks[label] = task_id
        self._progress.update(task_id, completed=cur, total=total)
        # A live progress bar supersedes any in-between status spinner.
        self._status_active = False

    def log(self, msg):
        text = str(msg)
        self._console.log(text)
        if text.endswith("..."):
            self._status.update(text)
            self._status_active = True
        else:
            self._status_active = False


@contextmanager
def cli_reporter():
    """Yield `(log_fn, progress_fn)` for use with `run_program` /
    `run_convert` and friends."""
    if not sys.stdout.isatty():
        yield (print, lambda *args, **kwargs: None)
        return

    display = _CliDisplay()
    live = Live(display, console=display.console, refresh_per_second=12)
    live.start()
    try:
        yield (display.log, display.update_progress)
    finally:
        live.stop()
