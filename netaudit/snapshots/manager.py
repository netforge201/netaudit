"""Snapshot creation/listing/loading for device state over time."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

TIMESTAMP_FORMAT = "%Y-%m-%d_%H%M%S"


@dataclass
class Snapshot:
    target: str
    timestamp: str
    path: Path
    files: dict[str, str]  # filename -> content


class SnapshotError(RuntimeError):
    """Raised for snapshot creation/loading failures."""


def snapshot_dir_for(base_dir: Path, target: str) -> Path:
    return base_dir / target


def create_snapshot(base_dir: Path, target: str, files: dict[str, str]) -> Snapshot:
    """Persist a new snapshot of ``files`` (label -> raw text) for ``target``."""
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    directory = snapshot_dir_for(base_dir, target) / timestamp
    directory.mkdir(parents=True, exist_ok=True)

    for label, content in files.items():
        filename = f"{label}.txt"
        (directory / filename).write_text(content, encoding="utf-8")

    return Snapshot(target=target, timestamp=timestamp, path=directory, files=files)


def list_snapshots(base_dir: Path, target: str | None = None) -> list[tuple[str, str, Path]]:
    """List available snapshots as (target, timestamp, path) tuples, newest first."""
    results: list[tuple[str, str, Path]] = []
    if not base_dir.exists():
        return results

    targets = [base_dir / target] if target else list(base_dir.iterdir())
    for target_dir in targets:
        if not target_dir.is_dir():
            continue
        for snap_dir in target_dir.iterdir():
            if snap_dir.is_dir():
                results.append((target_dir.name, snap_dir.name, snap_dir))

    results.sort(key=lambda t: t[1], reverse=True)
    return results


def load_snapshot(path: Path) -> dict[str, str]:
    """Load all label -> content files from a snapshot directory."""
    if not path.exists():
        raise SnapshotError(f"Snapshot not found: {path}")
    files: dict[str, str] = {}
    for file in sorted(path.glob("*.txt")):
        files[file.stem] = file.read_text(encoding="utf-8")
    return files


def latest_snapshots(base_dir: Path, target: str, count: int = 2) -> list[Path]:
    """Return the ``count`` most recent snapshot directories for ``target``."""
    snaps = list_snapshots(base_dir, target)
    return [path for _, _, path in snaps[:count]]
