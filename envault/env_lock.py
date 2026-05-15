"""env_lock.py — Lock/unlock vault access with a session token stored locally."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

LOCK_FILENAME = ".envault_lock"
DEFAULT_TTL_SECONDS = 3600  # 1 hour


class LockError(Exception):
    """Raised on lock/unlock failures."""


def _lock_path(vault_path: Path) -> Path:
    return vault_path.parent / LOCK_FILENAME


def _token(passphrase: str, vault_path: Path) -> str:
    """Derive a deterministic session token from passphrase + vault path."""
    raw = f"{passphrase}:{vault_path.resolve()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def lock_vault(vault_path: Path, passphrase: str, ttl: int = DEFAULT_TTL_SECONDS) -> Path:
    """Create a session lock file granting passphrase-free access for *ttl* seconds.

    Returns the path to the lock file.
    """
    if not vault_path.exists():
        raise LockError(f"Vault not found: {vault_path}")
    if ttl <= 0:
        raise LockError("TTL must be a positive integer.")

    lock_file = _lock_path(vault_path)
    payload = {
        "token": _token(passphrase, vault_path),
        "expires_at": time.time() + ttl,
        "vault": str(vault_path.resolve()),
    }
    lock_file.write_text(json.dumps(payload), encoding="utf-8")
    return lock_file


def unlock_vault(vault_path: Path) -> None:
    """Remove the session lock file, forcing passphrase entry on next access."""
    lock_file = _lock_path(vault_path)
    if lock_file.exists():
        lock_file.unlink()


def is_locked(vault_path: Path, passphrase: str) -> bool:
    """Return True if a valid, non-expired session lock exists for *passphrase*."""
    lock_file = _lock_path(vault_path)
    if not lock_file.exists():
        return False
    try:
        payload = json.loads(lock_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    if time.time() > payload.get("expires_at", 0):
        # Expired — clean up silently
        try:
            lock_file.unlink()
        except OSError:
            pass
        return False

    return payload.get("token") == _token(passphrase, vault_path)


def lock_status(vault_path: Path) -> dict:
    """Return a dict describing the current lock state (for CLI display)."""
    lock_file = _lock_path(vault_path)
    if not lock_file.exists():
        return {"locked": False}
    try:
        payload = json.loads(lock_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"locked": False}

    expires_at = payload.get("expires_at", 0)
    remaining = max(0.0, expires_at - time.time())
    return {
        "locked": remaining > 0,
        "expires_at": expires_at,
        "remaining_seconds": int(remaining),
    }
