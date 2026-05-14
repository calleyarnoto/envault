"""Key rotation support for envault vaults."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.audit import AuditLog
from envault.vault import Vault, VaultError


class RotationError(VaultError):
    """Raised when key rotation fails."""


def rotate_passphrase(
    vault_path: Path,
    old_passphrase: str,
    new_passphrase: str,
    audit_log: Optional[AuditLog] = None,
    actor: str = "cli",
) -> int:
    """Re-encrypt all secrets in *vault_path* under *new_passphrase*.

    Returns the number of secrets that were re-encrypted.
    Raises :class:`RotationError` if the vault cannot be opened or saved.
    """
    if not vault_path.exists():
        raise RotationError(f"Vault not found: {vault_path}")

    if old_passphrase == new_passphrase:
        raise RotationError("New passphrase must differ from the old one.")

    # Load with the old passphrase — this also validates it.
    vault = Vault(vault_path, old_passphrase)
    try:
        vault.load()
    except VaultError as exc:
        raise RotationError(f"Could not open vault: {exc}") from exc

    secrets = {key: vault.get(key) for key in vault.list()}
    count = len(secrets)

    # Swap passphrase and persist.
    vault.passphrase = new_passphrase
    try:
        vault.save()
    except VaultError as exc:
        raise RotationError(f"Could not save rotated vault: {exc}") from exc

    if audit_log is not None:
        audit_log.append(
            action="rotate",
            key="*",
            actor=actor,
            metadata={"secrets_rotated": count},
        )

    return count
