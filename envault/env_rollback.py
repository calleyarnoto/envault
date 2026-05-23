"""Rollback a vault to a previous snapshot by index or label."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.snapshot import SnapshotError, list_snapshots, restore_snapshot
from envault.vault import Vault, VaultError


class RollbackError(Exception):
    """Raised when a rollback operation fails."""


def list_rollback_points(vault_path: Path) -> list[dict]:
    """Return available rollback points (snapshots) for *vault_path*.

    Each entry is a dict with keys: ``index``, ``label``, ``path``.
    Index 0 is the most-recent snapshot.
    """
    if not vault_path.exists():
        raise RollbackError(f"Vault not found: {vault_path}")

    snapshots = list_snapshots(vault_path)
    return [
        {"index": i, "label": snap.stem, "path": snap}
        for i, snap in enumerate(snapshots)
    ]


def rollback_vault(
    vault_path: Path,
    passphrase: str,
    *,
    index: Optional[int] = None,
    label: Optional[str] = None,
) -> dict:
    """Restore *vault_path* to a previous snapshot.

    Exactly one of *index* or *label* must be supplied.

    Returns a summary dict with keys:
    ``snapshot_label``, ``secrets_restored``, ``snapshot_path``.
    """
    if (index is None) == (label is None):
        raise RollbackError("Provide exactly one of 'index' or 'label'.")

    if not vault_path.exists():
        raise RollbackError(f"Vault not found: {vault_path}")

    points = list_rollback_points(vault_path)
    if not points:
        raise RollbackError("No snapshots available to roll back to.")

    if index is not None:
        if index < 0 or index >= len(points):
            raise RollbackError(
                f"Index {index} out of range (0–{len(points) - 1})."
            )
        chosen = points[index]
    else:
        matches = [p for p in points if label in p["label"]]
        if not matches:
            raise RollbackError(f"No snapshot found matching label '{label}'.")
        chosen = matches[0]

    try:
        restore_snapshot(chosen["path"], vault_path, passphrase)
    except SnapshotError as exc:
        raise RollbackError(str(exc)) from exc

    try:
        vault = Vault(vault_path, passphrase)
        vault.load()
        count = len(vault.secrets)
    except VaultError as exc:
        raise RollbackError(f"Vault unreadable after rollback: {exc}") from exc

    return {
        "snapshot_label": chosen["label"],
        "secrets_restored": count,
        "snapshot_path": chosen["path"],
    }
