from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    log = Signal(str)
    progress = Signal(int, int, str)
    finished_with_result = Signal(bool, str)

    def __init__(self, target, kwargs, with_progress: bool = True):
        super().__init__()
        self._target = target
        self._kwargs = kwargs
        self._with_progress = with_progress

    def run(self):
        try:
            kwargs = dict(self._kwargs, log_fn=self.log.emit)
            if self._with_progress:
                kwargs["progress_fn"] = self.progress.emit
            self._target(**kwargs)
            self.finished_with_result.emit(True, "Finished")
        except Exception as e:
            self.finished_with_result.emit(False, f"{type(e).__name__}: {e}")
