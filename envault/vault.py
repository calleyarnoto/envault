"""Vault — stores and retrieves encrypted secrets for a project."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterator, Optional

from envault.audit import append_audit_entry
from envault.crypto import decrypt, encrypt

VAULT_VERSION = 1


class VaultError(Exception):
    """Raised when a vault operation fails."""


class Vault:
    """Manages an encrypted secrets vault on disk."""

    def __init__(self, path: Path, passphrase: str):
        self._path = Path(path)
        self._passphrase = passphrase
        self._secrets: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def init(cls, path: Path, passphrase: str) -> "Vault":
        """Create a new, empty vault file."""
        path = Path(path)
        if path.exists():
            raise VaultError(f"Vault already exists at {path}")
        vault = cls(path, passphrase)
        vault.save()
        append_audit_entry(path, action="init")
        return vault

    @classmethod
    def load(cls, path: Path, passphrase: str) -> "Vault":
        """Load and decrypt an existing vault file."""
        path = Path(path)
        if not path.exists():
            raise VaultError(f"No vault found at {path}")
        raw = path.read_text(encoding="utf-8")
        try:
            payload = json.loads(raw)
            plaintext = decrypt(payload["data"], passphrase)
            secrets = json.loads(plaintext)
        except Exception as exc:
            raise VaultError(f"Failed to open vault: {exc}") from exc
        vault = cls(path, passphrase)
        vault._secrets = secrets
        return vault

    def save(self) -> None:
        """Encrypt and write the vault to disk."""
        plaintext = json.dumps(self._secrets)
        ciphertext = encrypt(plaintext, self._passphrase)
        payload = {"version": VAULT_VERSION, "data": ciphertext}
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Secret management
    # ------------------------------------------------------------------

    def set(self, key: str, value: str) -> None:
        """Store a secret and persist the vault."""
        self._secrets[key] = value
        self.save()
        append_audit_entry(self._path, action="set", key=key)

    def get(self, key: str) -> str:
        """Retrieve a secret by key."""
        if key not in self._secrets:
            raise VaultError(f"Key not found: {key!r}")
        append_audit_entry(self._path, action="get", key=key)
        return self._secrets[key]

    def delete(self, key: str) -> None:
        """Remove a secret from the vault."""
        if key not in self._secrets:
            raise VaultError(f"Key not found: {key!r}")
        del self._secrets[key]
        self.save()
        append_audit_entry(self._path, action="delete", key=key)

    def list_keys(self) -> list[str]:
        """Return sorted list of all secret keys."""
        return sorted(self._secrets)

    def __iter__(self) -> Iterator[tuple[str, str]]:
        yield from self._secrets.items()

    def __len__(self) -> int:
        return len(self._secrets)
