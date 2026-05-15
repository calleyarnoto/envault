"""Backup and restore vault files with optional compression."""

from __future__ import annotations

import gzip
import shutil
import time
from pathlib import Path

BACKUP_SUFFIX = ".bak"
_BACKUP_DIR_NAME = ".envault_backups"


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""


def _backup_dir(vault_path: Path) -> Path:
    return vault_path.parent / _BACKUP_DIR_NAME


def create_backup(vault_path: Path, label: str = "", compress: bool = True) -> Path:
    """Copy *vault_path* into the backup directory and return the backup path.

    Parameters
    ----------
    vault_path:
        Path to the existing vault file.
    label:
        Optional human-readable label embedded in the filename.
    compress:
        When *True* (default) the backup is gzip-compressed.
    """
    if not vault_path.exists():
        raise BackupError(f"Vault file not found: {vault_path}")

    backup_dir = _backup_dir(vault_path)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    slug = f"_{label}" if label else ""
    ext = ".gz" if compress else ""
    filename = f"{vault_path.stem}{slug}_{timestamp}{BACKUP_SUFFIX}{ext}"
    dest = backup_dir / filename

    if compress:
        with vault_path.open("rb") as src, gzip.open(dest, "wb") as dst:
            shutil.copyfileobj(src, dst)
    else:
        shutil.copy2(vault_path, dest)

    return dest


def list_backups(vault_path: Path) -> list[Path]:
    """Return backup paths sorted oldest-first."""
    backup_dir = _backup_dir(vault_path)
    if not backup_dir.exists():
        return []
    files = sorted(backup_dir.glob(f"{vault_path.stem}*{BACKUP_SUFFIX}*"))
    return files


def restore_backup(backup_path: Path, vault_path: Path, overwrite: bool = False) -> None:
    """Restore a backup file to *vault_path*.

    Parameters
    ----------
    backup_path:
        Path to the backup file (may be gzip-compressed).
    vault_path:
        Destination vault path.
    overwrite:
        If *False* (default) raises :class:`BackupError` when the vault already exists.
    """
    if not backup_path.exists():
        raise BackupError(f"Backup file not found: {backup_path}")
    if vault_path.exists() and not overwrite:
        raise BackupError(
            f"Vault already exists at {vault_path}. Pass overwrite=True to replace it."
        )

    if backup_path.suffix == ".gz":
        with gzip.open(backup_path, "rb") as src, vault_path.open("wb") as dst:
            shutil.copyfileobj(src, dst)
    else:
        shutil.copy2(backup_path, vault_path)
