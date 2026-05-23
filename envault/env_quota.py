"""Per-vault secret quota enforcement."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envault.vault import Vault, VaultError


class QuotaError(Exception):
    """Raised when a quota operation fails."""


DEFAULT_MAX_SECRETS = 100


def _quota_path(vault_path: Path) -> Path:
    return vault_path.parent / (vault_path.stem + ".quota.json")


def _load_quota(vault_path: Path) -> dict:
    p = _quota_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_quota(vault_path: Path, data: dict) -> None:
    _quota_path(vault_path).write_text(json.dumps(data, indent=2))


def set_quota(vault_path: Path, max_secrets: int) -> int:
    """Set the maximum number of secrets allowed in the vault."""
    if not vault_path.exists():
        raise QuotaError(f"Vault not found: {vault_path}")
    if max_secrets < 1:
        raise QuotaError("max_secrets must be at least 1")
    data = _load_quota(vault_path)
    data["max_secrets"] = max_secrets
    _save_quota(vault_path, data)
    return max_secrets


def get_quota(vault_path: Path) -> Optional[int]:
    """Return the configured quota, or None if not set."""
    data = _load_quota(vault_path)
    return data.get("max_secrets")


def check_quota(vault_path: Path, passphrase: str) -> dict:
    """Return quota status: current count, limit, and whether limit is reached."""
    if not vault_path.exists():
        raise QuotaError(f"Vault not found: {vault_path}")
    try:
        vault = Vault(vault_path, passphrase)
        secrets = vault.list()
    except VaultError as exc:
        raise QuotaError(str(exc)) from exc
    current = len(secrets)
    limit = get_quota(vault_path)
    return {
        "current": current,
        "limit": limit,
        "at_limit": limit is not None and current >= limit,
    }


def enforce_quota(vault_path: Path, passphrase: str) -> None:
    """Raise QuotaError if the vault is at or over its quota."""
    status = check_quota(vault_path, passphrase)
    if status["at_limit"]:
        raise QuotaError(
            f"Quota reached: {status['current']}/{status['limit']} secrets stored."
        )


def clear_quota(vault_path: Path) -> None:
    """Remove the quota setting for the vault."""
    p = _quota_path(vault_path)
    if p.exists():
        p.unlink()
