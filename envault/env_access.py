"""Access control for vault secrets — restrict which keys a given role/identity can read or write."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

ACCESS_FILENAME = ".envault_access.json"


class AccessError(Exception):
    """Raised when an access-control operation fails."""


def _access_path(vault_path: Path) -> Path:
    return vault_path.parent / ACCESS_FILENAME


def _load_access_map(vault_path: Path) -> Dict[str, Dict]:
    p = _access_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_access_map(vault_path: Path, data: Dict[str, Dict]) -> None:
    _access_path(vault_path).write_text(json.dumps(data, indent=2))


def grant_access(vault_path: Path, role: str, keys: List[str], permission: str = "read") -> int:
    """Grant *role* access to *keys* with *permission* (read|write).

    Returns the number of keys newly granted.
    """
    if not vault_path.exists():
        raise AccessError(f"Vault not found: {vault_path}")
    if not role.strip():
        raise AccessError("Role must not be empty.")
    if permission not in ("read", "write"):
        raise AccessError(f"Invalid permission '{permission}'; must be 'read' or 'write'.")
    if not keys:
        raise AccessError("At least one key must be specified.")

    data = _load_access_map(vault_path)
    entry = data.setdefault(role, {"read": [], "write": []})
    added = 0
    for key in keys:
        if key not in entry[permission]:
            entry[permission].append(key)
            added += 1
    _save_access_map(vault_path, data)
    return added


def revoke_access(vault_path: Path, role: str, keys: List[str], permission: str = "read") -> int:
    """Revoke *role*'s access to *keys* for *permission*.

    Returns the number of keys revoked.
    """
    if not vault_path.exists():
        raise AccessError(f"Vault not found: {vault_path}")
    if permission not in ("read", "write"):
        raise AccessError(f"Invalid permission '{permission}'; must be 'read' or 'write'.")

    data = _load_access_map(vault_path)
    entry = data.get(role)
    if entry is None:
        return 0
    removed = 0
    for key in keys:
        if key in entry.get(permission, []):
            entry[permission].remove(key)
            removed += 1
    _save_access_map(vault_path, data)
    return removed


def list_access(vault_path: Path, role: Optional[str] = None) -> Dict[str, Dict]:
    """Return the full access map, or just the entry for *role* if given."""
    data = _load_access_map(vault_path)
    if role is not None:
        return {role: data.get(role, {"read": [], "write": []})}
    return data


def can_access(vault_path: Path, role: str, key: str, permission: str = "read") -> bool:
    """Return True if *role* has *permission* on *key*."""
    data = _load_access_map(vault_path)
    entry = data.get(role, {})
    return key in entry.get(permission, [])
