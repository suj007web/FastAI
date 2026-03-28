from __future__ import annotations

from pathlib import Path

from fastai.app.ingestion_watcher import DocsIngestionWatcher


def test_docs_watcher_triggers_on_create_modify_delete(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    triggered: list[str] = []

    watcher = DocsIngestionWatcher(
        docs_path=docs_dir,
        on_change=lambda: triggered.append("run"),
        poll_interval_sec=0.1,
        debounce_sec=0.0,
    )

    # First scan captures baseline and does not trigger.
    watcher._last_snapshot = watcher._take_snapshot()
    assert watcher.poll_once() is False

    target = docs_dir / "guide.txt"
    target.write_text("alpha", encoding="utf-8")
    assert watcher.poll_once() is True
    assert len(triggered) == 1

    target.write_text("alpha beta", encoding="utf-8")
    assert watcher.poll_once() is True
    assert len(triggered) == 2

    target.unlink()
    assert watcher.poll_once() is True
    assert len(triggered) == 3


def test_docs_watcher_ignores_when_snapshot_unchanged(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    runs: list[str] = []
    watcher = DocsIngestionWatcher(
        docs_path=docs_dir,
        on_change=lambda: runs.append("run"),
        poll_interval_sec=0.1,
        debounce_sec=0.0,
    )

    watcher._last_snapshot = watcher._take_snapshot()
    assert watcher.poll_once() is False
    assert runs == []
