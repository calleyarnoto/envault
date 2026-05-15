"""Tests for envault.env_backup."""

from __future__ import annotations

import gzip
import json
import pytest
from pathlib import Path

from envault.env_backup import (
    BackupError,
    create_backup,
    list_backups,
    restore_backup,
    BACKUP_SUFFIX,
    _backup_dir,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "vault.json"
    p.write_text(json.dumps({"secrets": {"KEY": "val"}, "version": 1}))
    return p


# ---------------------------------------------------------------------------
# create_backup
# ---------------------------------------------------------------------------

def test_create_backup_returns_path_inside_backup_dir(vault_file: Path) -> None:
    dest = create_backup(vault_file)
    assert dest.parent == _backup_dir(vault_file)


def test_create_backup_filename_contains_suffix(vault_file: Path) -> None:
    dest = create_backup(vault_file)
    assert BACKUP_SUFFIX in dest.name


def test_create_backup_filename_contains_label(vault_file: Path) -> None:
    dest = create_backup(vault_file, label="pre-deploy")
    assert "pre-deploy" in dest.name


def test_create_backup_compressed_by_default(vault_file: Path) -> None:
    dest = create_backup(vault_file)
    assert dest.suffix == ".gz"
    # Must be valid gzip
    with gzip.open(dest, "rb") as f:
        content = f.read()
    assert b"secrets" in content


def test_create_backup_uncompressed(vault_file: Path) -> None:
    dest = create_backup(vault_file, compress=False)
    assert dest.suffix != ".gz"
    assert b"secrets" in dest.read_bytes()


def test_create_backup_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="not found"):
        create_backup(tmp_path / "missing.json")


# ---------------------------------------------------------------------------
# list_backups
# ---------------------------------------------------------------------------

def test_list_backups_empty_when_no_dir(vault_file: Path) -> None:
    assert list_backups(vault_file) == []


def test_list_backups_returns_created_backup(vault_file: Path) -> None:
    dest = create_backup(vault_file)
    backups = list_backups(vault_file)
    assert dest in backups


def test_list_backups_sorted_oldest_first(vault_file: Path) -> None:
    a = create_backup(vault_file, label="a")
    b = create_backup(vault_file, label="b")
    backups = list_backups(vault_file)
    assert backups.index(a) < backups.index(b)


# ---------------------------------------------------------------------------
# restore_backup
# ---------------------------------------------------------------------------

def test_restore_backup_recreates_vault(vault_file: Path, tmp_path: Path) -> None:
    dest = create_backup(vault_file)
    target = tmp_path / "restored.json"
    restore_backup(dest, target)
    data = json.loads(target.read_text())
    assert data["secrets"]["KEY"] == "val"


def test_restore_backup_raises_if_exists_no_overwrite(vault_file: Path) -> None:
    dest = create_backup(vault_file)
    with pytest.raises(BackupError, match="already exists"):
        restore_backup(dest, vault_file)


def test_restore_backup_overwrite_flag(vault_file: Path) -> None:
    dest = create_backup(vault_file)
    restore_backup(dest, vault_file, overwrite=True)
    assert vault_file.exists()


def test_restore_backup_missing_backup_raises(tmp_path: Path, vault_file: Path) -> None:
    with pytest.raises(BackupError, match="not found"):
        restore_backup(tmp_path / "ghost.bak.gz", vault_file, overwrite=True)
