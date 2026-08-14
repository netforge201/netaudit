"""Tests for netaudit.snapshots (manager + differ)."""
from __future__ import annotations

import time
from pathlib import Path

from netaudit.snapshots.differ import diff_snapshots, diff_text
from netaudit.snapshots.manager import (
    create_snapshot,
    latest_snapshots,
    list_snapshots,
    load_snapshot,
)


def test_create_and_load_snapshot(tmp_path: Path):
    snap = create_snapshot(tmp_path, "10.0.0.1", {"version": "IOS 15.2", "arp": "a b c"})
    assert snap.path.exists()
    loaded = load_snapshot(snap.path)
    assert loaded["version"] == "IOS 15.2"
    assert loaded["arp"] == "a b c"


def test_list_snapshots_empty(tmp_path: Path):
    assert list_snapshots(tmp_path) == []


def test_list_snapshots_filters_by_target(tmp_path: Path):
    create_snapshot(tmp_path, "10.0.0.1", {"version": "v1"})
    create_snapshot(tmp_path, "10.0.0.2", {"version": "v1"})
    all_snaps = list_snapshots(tmp_path)
    assert len(all_snaps) == 2
    filtered = list_snapshots(tmp_path, "10.0.0.1")
    assert len(filtered) == 1
    assert filtered[0][0] == "10.0.0.1"


def test_latest_snapshots_ordering(tmp_path: Path):
    create_snapshot(tmp_path, "10.0.0.1", {"version": "v1"})
    time.sleep(1.1)  # ensure distinct second-resolution timestamps
    create_snapshot(tmp_path, "10.0.0.1", {"version": "v2"})

    latest = latest_snapshots(tmp_path, "10.0.0.1", count=2)
    assert len(latest) == 2
    newest = load_snapshot(latest[0])
    oldest = load_snapshot(latest[1])
    assert newest["version"] == "v2"
    assert oldest["version"] == "v1"


class TestDiffText:
    def test_added_and_removed(self):
        added, removed = diff_text(["a", "b"], ["b", "c"])
        assert added == ["c"]
        assert removed == ["a"]

    def test_no_changes(self):
        added, removed = diff_text(["a", "b"], ["a", "b"])
        assert added == []
        assert removed == []

    def test_ignores_blank_lines(self):
        added, removed = diff_text(["a", "", "  "], ["a"])
        assert added == []
        assert removed == []


class TestDiffSnapshots:
    def test_detects_interface_change(self):
        old = {"interfaces": "Gi1/0/1 up\nGi1/0/2 up\n"}
        new = {"interfaces": "Gi1/0/1 up\nGi1/0/3 up\n"}
        result = diff_snapshots("t1", old, "t2", new)
        assert len(result.file_diffs) == 1
        fd = result.file_diffs[0]
        assert fd.label == "interfaces"
        assert "Gi1/0/3 up" in fd.added
        assert "Gi1/0/2 up" in fd.removed
        assert result.total_added == 1
        assert result.total_removed == 1

    def test_identical_files_produce_no_diff(self):
        files = {"arp": "a\nb\n"}
        result = diff_snapshots("t1", files, "t2", dict(files))
        assert result.file_diffs == []

    def test_new_file_appearing(self):
        old = {"version": "v1"}
        new = {"version": "v1", "arp": "a\n"}
        result = diff_snapshots("t1", old, "t2", new)
        labels = [f.label for f in result.file_diffs]
        assert "arp" in labels
