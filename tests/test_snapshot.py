"""Tests for envault.snapshot module."""

import time
from pathlib import Path

import pytest

from envault.snapshot import (
    SnapshotError,
    list_snapshots,
    restore_snapshot,
    save_snapshot,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    """A minimal fake vault file."""
    vf = tmp_path / "vault.json"
    vf.write_text('{"secrets": {}}')
    return vf


def test_save_snapshot_creates_file(vault_file: Path) -> None:
    snap = save_snapshot(vault_file, label="initial")
    assert snap.exists()


def test_save_snapshot_returns_path_inside_snapshot_dir(vault_file: Path) -> None:
    snap = save_snapshot(vault_file)
    assert snap.parent.name == ".envault_snapshots"


def test_save_snapshot_filename_contains_label(vault_file: Path) -> None:
    snap = save_snapshot(vault_file, label="before deploy")
    assert "before_deploy" in snap.name


def test_save_snapshot_filename_contains_timestamp(vault_file: Path) -> None:
    before = int(time.time())
    snap = save_snapshot(vault_file)
    ts_str = snap.stem.split("_")[0]
    assert int(ts_str) >= before


def test_save_snapshot_preserves_content(vault_file: Path) -> None:
    original = vault_file.read_bytes()
    snap = save_snapshot(vault_file)
    assert snap.read_bytes() == original


def test_save_snapshot_raises_if_vault_missing(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.json"
    with pytest.raises(SnapshotError, match="Vault not found"):
        save_snapshot(missing)


def test_list_snapshots_empty_when_no_directory(vault_file: Path) -> None:
    assert list_snapshots(vault_file) == []


def test_list_snapshots_returns_entries(vault_file: Path) -> None:
    save_snapshot(vault_file, label="a")
    save_snapshot(vault_file, label="b")
    entries = list_snapshots(vault_file)
    assert len(entries) == 2


def test_list_snapshots_sorted_newest_first(vault_file: Path) -> None:
    save_snapshot(vault_file, label="first")
    time.sleep(0.01)
    save_snapshot(vault_file, label="second")
    entries = list_snapshots(vault_file)
    ts0 = int(entries[0]["timestamp"])
    ts1 = int(entries[1]["timestamp"])
    assert ts0 >= ts1


def test_list_snapshots_entry_has_expected_keys(vault_file: Path) -> None:
    save_snapshot(vault_file)
    entry = list_snapshots(vault_file)[0]
    assert {"filename", "path", "timestamp"} <= entry.keys()


def test_restore_snapshot_overwrites_vault(vault_file: Path) -> None:
    snap = save_snapshot(vault_file, label="clean")
    vault_file.write_text('{"secrets": {"KEY": "val"}}')
    restore_snapshot(vault_file, snap)
    assert vault_file.read_text() == '{"secrets": {}}'


def test_restore_snapshot_raises_if_snapshot_missing(vault_file: Path) -> None:
    missing_snap = vault_file.parent / ".envault_snapshots" / "ghost.json"
    with pytest.raises(SnapshotError, match="Snapshot not found"):
        restore_snapshot(vault_file, missing_snap)
