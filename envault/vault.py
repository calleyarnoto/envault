"""Vault management: read, write, and manage encrypted .env vault files."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import encrypt, decrypt

DEFAULT_VAULT_FILENAME = ".envault"


class VaultError(Exception):
    """Raised when a vault operation fails."""


class Vault:
    """Represents an encrypted vault for a project's environment secrets."""

    def __init__(self, path: Path, passphrase: str) -> None:
        self.path = Path(path)
        self._passphrase = passphrase
        self._secrets: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load and decrypt secrets from the vault file."""
        if not self.path.exists():
            raise VaultError(f"Vault file not found: {self.path}")
        ciphertext = self.path.read_text(encoding="utf-8").strip()
        try:
            plaintext = decrypt(ciphertext, self._passphrase)
        except Exception as exc:
            raise VaultError(f"Failed to decrypt vault: {exc}") from exc
        try:
            self._secrets = json.loads(plaintext)
        except json.JSONDecodeError as exc:
            raise VaultError(f"Vault payload is corrupted: {exc}") from exc

    def save(self) -> None:
        """Encrypt and persist secrets to the vault file."""
        plaintext = json.dumps(self._secrets, indent=2)
        ciphertext = encrypt(plaintext, self._passphrase)
        self.path.write_text(ciphertext + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Secret management
    # ------------------------------------------------------------------

    def set(self, key: str, value: str) -> None:
        """Add or update a secret."""
        self._secrets[key] = value

    def get(self, key: str) -> Optional[str]:
        """Return the value for *key*, or None if not present."""
        return self._secrets.get(key)

    def delete(self, key: str) -> bool:
        """Remove *key* from the vault. Returns True if it existed."""
        return self._secrets.pop(key, None) is not None

    def list_keys(self):
        """Return a sorted list of all secret keys."""
        return sorted(self._secrets.keys())

    def export_env(self) -> str:
        """Return secrets formatted as shell export statements."""
        lines = [f'export {k}="{v}"' for k, v in sorted(self._secrets.items())]
        return os.linesep.join(lines)

    def __len__(self) -> int:
        return len(self._secrets)


def init_vault(path: Path, passphrase: str) -> Vault:
    """Create a new, empty vault file at *path*."""
    if path.exists():
        raise VaultError(f"Vault already exists: {path}")
    vault = Vault(path, passphrase)
    vault.save()
    return vault
