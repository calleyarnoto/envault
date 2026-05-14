"""Secure secret sharing: export an encrypted share bundle for a subset of keys."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional

from envault.crypto import encrypt, decrypt
from envault.vault import Vault, VaultError


class ShareError(Exception):
    """Raised when a share operation fails."""


def create_share(
    vault_path: Path,
    passphrase: str,
    keys: List[str],
    share_passphrase: str,
    label: Optional[str] = None,
) -> str:
    """Encrypt a subset of secrets into a portable share bundle (JSON string).

    The bundle is encrypted with *share_passphrase* so it can be transmitted
    safely.  Returns the bundle as a JSON string.
    """
    vault = Vault(vault_path)
    try:
        vault.load(passphrase)
    except VaultError as exc:
        raise ShareError(f"Cannot open vault: {exc}") from exc

    missing = [k for k in keys if k not in vault.secrets]
    if missing:
        raise ShareError(f"Keys not found in vault: {', '.join(missing)}")

    subset = {k: vault.secrets[k] for k in keys}
    payload = json.dumps(
        {
            "label": label or "",
            "created_at": time.time(),
            "secrets": subset,
        }
    )
    return encrypt(payload, share_passphrase)


def read_share(bundle: str, share_passphrase: str) -> dict:
    """Decrypt a share bundle and return the contained secrets dict.

    Raises *ShareError* if the passphrase is wrong or the bundle is corrupted.
    """
    try:
        raw = decrypt(bundle, share_passphrase)
    except Exception as exc:
        raise ShareError(f"Failed to decrypt share bundle: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ShareError("Share bundle payload is not valid JSON.") from exc

    if "secrets" not in data:
        raise ShareError("Share bundle is missing 'secrets' field.")

    return data["secrets"]


def import_share(
    bundle: str,
    share_passphrase: str,
    vault_path: Path,
    passphrase: str,
    overwrite: bool = False,
) -> int:
    """Import secrets from a share bundle into an existing vault.

    Returns the number of secrets written.  Raises *ShareError* on conflict
    when *overwrite* is False.
    """
    secrets = read_share(bundle, share_passphrase)

    vault = Vault(vault_path)
    try:
        vault.load(passphrase)
    except VaultError as exc:
        raise ShareError(f"Cannot open vault: {exc}") from exc

    conflicts = [k for k in secrets if k in vault.secrets and not overwrite]
    if conflicts:
        raise ShareError(
            f"Keys already exist (use overwrite=True): {', '.join(conflicts)}"
        )

    for k, v in secrets.items():
        vault.set(passphrase, k, v)

    return len(secrets)
