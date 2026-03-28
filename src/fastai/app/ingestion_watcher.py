"""Background docs watcher that triggers ingestion when files change."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

LOGGER = logging.getLogger("fastai.ingestion")


@dataclass(frozen=True)
class FileSnapshot:
    """Stable file identity used to detect file system changes."""

    path: str
    modified_ns: int
    size: int


@dataclass
class DocsIngestionWatcher:
    """Polls a docs directory and runs ingestion when changes are detected."""

    docs_path: Path
    on_change: Callable[[], None]
    poll_interval_sec: float = 2.0
    debounce_sec: float = 1.0
    _last_snapshot: tuple[FileSnapshot, ...] = field(default_factory=tuple, init=False)
    _last_trigger_monotonic: float = field(default=0.0, init=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)

    def start(self) -> None:
        """Start the watcher thread if it is not already running."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._last_snapshot = self._take_snapshot()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="fastai-docs-watcher")
        self._thread.start()

    def stop(self) -> None:
        """Stop the watcher thread and wait briefly for shutdown."""
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        self._thread = None

    def poll_once(self) -> bool:
        """Run one scan cycle and trigger ingestion if the snapshot changed."""
        current_snapshot = self._take_snapshot()
        if current_snapshot == self._last_snapshot:
            return False

        self._last_snapshot = current_snapshot
        now = time.monotonic()
        if now - self._last_trigger_monotonic < self.debounce_sec:
            return False

        self._last_trigger_monotonic = now
        try:
            self.on_change()
        except Exception:
            LOGGER.exception("Auto-ingestion failed after docs change detection.")
        return True

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self.poll_once()
            self._stop_event.wait(self.poll_interval_sec)

    def _take_snapshot(self) -> tuple[FileSnapshot, ...]:
        root = self.docs_path
        if not root.exists() or not root.is_dir():
            return ()

        snapshots: list[FileSnapshot] = []
        for file_path in sorted(path for path in root.rglob("*") if path.is_file()):
            stat = file_path.stat()
            relative_path = file_path.relative_to(root).as_posix()
            snapshots.append(
                FileSnapshot(
                    path=relative_path,
                    modified_ns=stat.st_mtime_ns,
                    size=stat.st_size,
                )
            )

        return tuple(snapshots)
