"""Snapshot support for envault — save and restore vault states."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

SNAPSHOT_DIR_NAME = ".envault_snapshots"


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshot_dir(vault_path: Path) -> Path:
    """Return the snapshot directory adjacent to the vault file."""
    return vault_path.parent / SNAPSHOT_DIR_NAME


def save_snapshot(vault_path: Path, label: Optional[str] = None) -> Path:
    """Persist a copy of the current vault file as a snapshot.

    Args:
        vault_path: Path to the existing vault file.
        label: Optional human-readable label embedded in the filename.

    Returns:
        Path to the newly created snapshot file.

    Raises:
        SnapshotError: If the vault file does not exist.
    """
    if not vault_path.exists():
        raise SnapshotError(f"Vault not found: {vault_path}")

    snap_dir = _snapshot_dir(vault_path)
    snap_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    safe_label = label.replace(" ", "_") if label else "snap"
    filename = f"{timestamp}_{safe_label}.json"
    snapshot_path = snap_dir / filename

    snapshot_path.write_bytes(vault_path.read_bytes())
    return snapshot_path


def list_snapshots(vault_path: Path) -> List[Dict[str, str]]:
    """Return metadata for all snapshots associated with a vault.

    Each entry contains ``filename``, ``path``, and ``timestamp`` keys.
    Results are sorted newest-first.
    """
    snap_dir = _snapshot_dir(vault_path)
    if not snap_dir.exists():
        return []

    entries = []
    for f in sorted(snap_dir.glob("*.json"), reverse=True):
        parts = f.stem.split("_", 1)
        ts = parts[0] if parts[0].isdigit() else "0"
        entries.append(
            {
                "filename": f.name,
                "path": str(f),
                "timestamp": ts,
            }
        )
    return entries


def restore_snapshot(vault_path: Path, snapshot_path: Path) -> None:
    """Overwrite the vault file with the contents of a snapshot.

    Args:
        vault_path: Destination vault file path.
        snapshot_path: Path to the snapshot file to restore.

    Raises:
        SnapshotError: If the snapshot file does not exist.
    """
    if not snapshot_path.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot_path}")

    vault_path.write_bytes(snapshot_path.read_bytes())
