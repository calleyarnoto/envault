"""Group management for envault secrets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault, VaultError


class GroupError(Exception):
    """Raised when a group operation fails."""


def _group_path(vault_path: Path) -> Path:
    return vault_path.parent / (vault_path.stem + ".groups.json")


def _load_groups(vault_path: Path) -> Dict[str, List[str]]:
    p = _group_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_groups(vault_path: Path, groups: Dict[str, List[str]]) -> None:
    _group_path(vault_path).write_text(json.dumps(groups, indent=2, sort_keys=True))


def create_group(vault_path: Path, group: str, keys: List[str], passphrase: str) -> int:
    """Create a named group containing *keys*. Returns the number of keys added."""
    if not group.strip():
        raise GroupError("Group name must not be empty.")
    if not vault_path.exists():
        raise GroupError(f"Vault not found: {vault_path}")
    vault = Vault(vault_path)
    secrets = vault.load(passphrase)
    missing = [k for k in keys if k not in secrets]
    if missing:
        raise GroupError(f"Keys not found in vault: {', '.join(missing)}")
    groups = _load_groups(vault_path)
    existing = set(groups.get(group, []))
    existing.update(keys)
    groups[group] = sorted(existing)
    _save_groups(vault_path, groups)
    return len(groups[group])


def delete_group(vault_path: Path, group: str) -> None:
    """Remove a group definition (does not delete the underlying secrets)."""
    groups = _load_groups(vault_path)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    del groups[group]
    _save_groups(vault_path, groups)


def list_groups(vault_path: Path) -> Dict[str, List[str]]:
    """Return all groups and their key lists, sorted."""
    return _load_groups(vault_path)


def get_group_secrets(vault_path: Path, group: str, passphrase: str) -> Dict[str, str]:
    """Return a dict of key→value for every key in *group*."""
    groups = _load_groups(vault_path)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    vault = Vault(vault_path)
    secrets = vault.load(passphrase)
    return {k: secrets[k] for k in groups[group] if k in secrets}
