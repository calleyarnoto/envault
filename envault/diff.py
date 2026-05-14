"""Diff two snapshots or a snapshot against the live vault."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from envault.snapshot import SnapshotError, restore_snapshot
from envault.vault import Vault


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class SecretDiff:
    """Represents a single secret change between two states."""

    key: str
    status: str  # 'added' | 'removed' | 'changed' | 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __repr__(self) -> str:
        if self.status == "added":
            return f"+ {self.key}"
        if self.status == "removed":
            return f"- {self.key}"
        if self.status == "changed":
            return f"~ {self.key}"
        return f"  {self.key}"


def diff_secrets(
    old: Dict[str, str],
    new: Dict[str, str],
    *,
    show_unchanged: bool = False,
) -> List[SecretDiff]:
    """Compare two secret dicts and return a list of SecretDiff entries."""
    results: List[SecretDiff] = []
    all_keys = sorted(set(old) | set(new))

    for key in all_keys:
        if key in old and key not in new:
            results.append(SecretDiff(key=key, status="removed", old_value=old[key]))
        elif key not in old and key in new:
            results.append(SecretDiff(key=key, status="added", new_value=new[key]))
        elif old[key] != new[key]:
            results.append(
                SecretDiff(key=key, status="changed", old_value=old[key], new_value=new[key])
            )
        elif show_unchanged:
            results.append(SecretDiff(key=key, status="unchanged"))

    return results


def diff_snapshot_vs_vault(
    snapshot_path: str,
    vault_path: str,
    passphrase: str,
    *,
    show_unchanged: bool = False,
) -> List[SecretDiff]:
    """Diff a saved snapshot against the current live vault."""
    try:
        snapshot_secrets = restore_snapshot(snapshot_path, passphrase)
    except SnapshotError as exc:
        raise DiffError(f"Could not load snapshot: {exc}") from exc

    try:
        vault = Vault(vault_path, passphrase)
        live_secrets = vault.list()
    except Exception as exc:
        raise DiffError(f"Could not load vault: {exc}") from exc

    return diff_secrets(snapshot_secrets, live_secrets, show_unchanged=show_unchanged)
