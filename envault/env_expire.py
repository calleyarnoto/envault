"""Secret expiry management — mark secrets with an expiry date and list/purge expired ones."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional, Tuple

from envault.vault import Vault, VaultError


class ExpireError(Exception):
    """Raised when an expiry operation fails."""


def _expire_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".expire.json")


def _load_expire_map(vault_path: Path) -> dict:
    p = _expire_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_expire_map(vault_path: Path, mapping: dict) -> None:
    _expire_path(vault_path).write_text(json.dumps(mapping, indent=2))


def set_expiry(vault_path: Path, key: str, days: float, passphrase: str) -> float:
    """Set an expiry *days* from now for *key*.  Returns the expiry timestamp."""
    if days <= 0:
        raise ExpireError("days must be a positive number")
    v = Vault(vault_path)
    v.load(passphrase)
    if key not in v.secrets:
        raise ExpireError(f"Key '{key}' not found in vault")
    expiry = time.time() + days * 86400
    mapping = _load_expire_map(vault_path)
    mapping[key] = expiry
    _save_expire_map(vault_path, mapping)
    return expiry


def get_expiry(vault_path: Path, key: str) -> Optional[float]:
    """Return the expiry timestamp for *key*, or None if not set."""
    return _load_expire_map(vault_path).get(key)


def list_expired(vault_path: Path, passphrase: str) -> List[Tuple[str, float]]:
    """Return list of (key, expiry_ts) pairs whose expiry has passed."""
    v = Vault(vault_path)
    v.load(passphrase)
    mapping = _load_expire_map(vault_path)
    now = time.time()
    return [(k, ts) for k, ts in mapping.items() if ts <= now and k in v.secrets]


def purge_expired(vault_path: Path, passphrase: str) -> List[str]:
    """Delete all expired secrets from the vault.  Returns list of purged keys."""
    expired = list_expired(vault_path, passphrase)
    if not expired:
        return []
    v = Vault(vault_path)
    v.load(passphrase)
    purged = []
    for key, _ in expired:
        if key in v.secrets:
            v.delete(key, passphrase)
            purged.append(key)
    mapping = _load_expire_map(vault_path)
    for key in purged:
        mapping.pop(key, None)
    _save_expire_map(vault_path, mapping)
    return purged
