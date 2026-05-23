"""Tests for envault.env_rollback."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.vault import Vault
from envault.snapshot import save_snapshot
from envault.env_rollback import RollbackError, list_rollback_points, rollback_vault

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "secrets.vault"
    v = Vault(path, PASS)
    v.init()
    v.set("ALPHA", "aaa")
    v.set("BETA", "bbb")
    v.save()
    return path


@pytest.fixture()
def vault_with_snapshot(vault_file: Path) -> Path:
    """Vault that already has one snapshot saved."""
    save_snapshot(vault_file, label="before")
    return vault_file


# ---------------------------------------------------------------------------
# list_rollback_points
# ---------------------------------------------------------------------------

def test_list_rollback_points_empty_when_no_snapshots(vault_file: Path):
    points = list_rollback_points(vault_file)
    assert points == []


def test_list_rollback_points_returns_entry(vault_with_snapshot: Path):
    points = list_rollback_points(vault_with_snapshot)
    assert len(points) == 1
    assert points[0]["index"] == 0
    assert "before" in points[0]["label"]
    assert isinstance(points[0]["path"], Path)


def test_list_rollback_points_missing_vault_raises(tmp_path: Path):
    with pytest.raises(RollbackError, match="not found"):
        list_rollback_points(tmp_path / "ghost.vault")


# ---------------------------------------------------------------------------
# rollback_vault — argument validation
# ---------------------------------------------------------------------------

def test_rollback_no_args_raises(vault_with_snapshot: Path):
    with pytest.raises(RollbackError, match="exactly one"):
        rollback_vault(vault_with_snapshot, PASS)


def test_rollback_both_args_raises(vault_with_snapshot: Path):
    with pytest.raises(RollbackError, match="exactly one"):
        rollback_vault(vault_with_snapshot, PASS, index=0, label="before")


def test_rollback_missing_vault_raises(tmp_path: Path):
    with pytest.raises(RollbackError, match="not found"):
        rollback_vault(tmp_path / "ghost.vault", PASS, index=0)


def test_rollback_no_snapshots_raises(vault_file: Path):
    with pytest.raises(RollbackError, match="No snapshots"):
        rollback_vault(vault_file, PASS, index=0)


def test_rollback_index_out_of_range_raises(vault_with_snapshot: Path):
    with pytest.raises(RollbackError, match="out of range"):
        rollback_vault(vault_with_snapshot, PASS, index=99)


def test_rollback_label_not_found_raises(vault_with_snapshot: Path):
    with pytest.raises(RollbackError, match="No snapshot found"):
        rollback_vault(vault_with_snapshot, PASS, label="nonexistent")


# ---------------------------------------------------------------------------
# rollback_vault — happy path
# ---------------------------------------------------------------------------

def test_rollback_by_index_returns_summary(vault_with_snapshot: Path):
    result = rollback_vault(vault_with_snapshot, PASS, index=0)
    assert result["secrets_restored"] >= 0
    assert "before" in result["snapshot_label"]
    assert isinstance(result["snapshot_path"], Path)


def test_rollback_by_label_restores_vault(vault_with_snapshot: Path):
    v = Vault(vault_with_snapshot, PASS)
    v.load()
    v.set("GAMMA", "ccc")
    v.save()

    result = rollback_vault(vault_with_snapshot, PASS, label="before")
    assert result["secrets_restored"] == 2  # ALPHA + BETA only

    v2 = Vault(vault_with_snapshot, PASS)
    v2.load()
    assert "GAMMA" not in v2.secrets
    assert v2.secrets["ALPHA"] == "aaa"
