"""TTL (time-to-live) support for vault secrets.

Allows setting an expiry on individual secrets so they are
automatically flagged or removed when they become stale.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

TTL_FILENAME = ".envault_ttl.json"


class TTLError(Exception):
    """Raised when a TTL operation fails."""


def _ttl_path(vault_path: Path) -> Path:
    return vault_path.parent / TTL_FILENAME


def _load_ttl_map(vault_path: Path) -> Dict[str, float]:
    p = _ttl_path(vault_path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise TTLError(f"Failed to read TTL file: {exc}") from exc


def _save_ttl_map(vault_path: Path, ttl_map: Dict[str, float]) -> None:
    p = _ttl_path(vault_path)
    try:
        p.write_text(json.dumps(ttl_map, indent=2))
    except OSError as exc:
        raise TTLError(f"Failed to write TTL file: {exc}") from exc


def set_ttl(vault_path: Path, key: str, seconds: float) -> float:
    """Set a TTL (in seconds from now) for *key*. Returns the expiry timestamp."""
    if seconds <= 0:
        raise TTLError("TTL must be a positive number of seconds.")
    ttl_map = _load_ttl_map(vault_path)
    expiry = time.time() + seconds
    ttl_map[key] = expiry
    _save_ttl_map(vault_path, ttl_map)
    return expiry


def get_ttl(vault_path: Path, key: str) -> Optional[float]:
    """Return the expiry timestamp for *key*, or None if no TTL is set."""
    return _load_ttl_map(vault_path).get(key)


def remove_ttl(vault_path: Path, key: str) -> bool:
    """Remove the TTL for *key*. Returns True if a TTL existed."""
    ttl_map = _load_ttl_map(vault_path)
    if key not in ttl_map:
        return False
    del ttl_map[key]
    _save_ttl_map(vault_path, ttl_map)
    return True


def expired_keys(vault_path: Path) -> List[str]:
    """Return a list of keys whose TTL has elapsed."""
    now = time.time()
    return [k for k, exp in _load_ttl_map(vault_path).items() if exp <= now]


def purge_expired(vault_path: Path, passphrase: str) -> List[str]:
    """Delete all expired keys from the vault and their TTL entries.

    Returns the list of deleted key names.
    """
    from envault.vault import Vault

    keys = expired_keys(vault_path)
    if not keys:
        return []
    vault = Vault.load(vault_path, passphrase)
    for k in keys:
        vault.delete(k)
    vault.save()
    ttl_map = _load_ttl_map(vault_path)
    for k in keys:
        ttl_map.pop(k, None)
    _save_ttl_map(vault_path, ttl_map)
    return keys
