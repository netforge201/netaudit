"""Line-based diffing between two device snapshots."""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field


@dataclass
class FileDiff:
    label: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class SnapshotDiff:
    old_timestamp: str
    new_timestamp: str
    file_diffs: list[FileDiff] = field(default_factory=list)

    @property
    def total_added(self) -> int:
        return sum(len(f.added) for f in self.file_diffs)

    @property
    def total_removed(self) -> int:
        return sum(len(f.removed) for f in self.file_diffs)

    @property
    def total_changed(self) -> int:
        return sum(len(f.changed) for f in self.file_diffs)


def diff_text(old_lines: list[str], new_lines: list[str]) -> tuple[list[str], list[str]]:
    """Return (added_lines, removed_lines) using a simple set-based diff.

    Lines are compared after stripping whitespace; order is not considered
    significant for 'show' command output like interface/ARP tables.
    """
    old_set = {l.strip() for l in old_lines if l.strip()}
    new_set = {l.strip() for l in new_lines if l.strip()}
    added = sorted(new_set - old_set)
    removed = sorted(old_set - new_set)
    return added, removed


def diff_snapshots(
    old_timestamp: str,
    old_files: dict[str, str],
    new_timestamp: str,
    new_files: dict[str, str],
) -> SnapshotDiff:
    """Compute a per-file diff between two loaded snapshots."""
    result = SnapshotDiff(old_timestamp=old_timestamp, new_timestamp=new_timestamp)
    labels = sorted(set(old_files) | set(new_files))

    for label in labels:
        old_content = old_files.get(label, "")
        new_content = new_files.get(label, "")
        if old_content == new_content:
            continue

        added, removed = diff_text(
            old_content.splitlines(), new_content.splitlines()
        )
        file_diff = FileDiff(label=label, added=added, removed=removed)
        result.file_diffs.append(file_diff)

    return result
