"""Rename a secret key inside a vault, preserving its value and metadata."""
from __future__ import annotations

from pathlib import Path

from envault.vault import Vault, VaultError
from envault.tags import _load_tag_map, _save_tag_map
from envault.ttl import _ttl_path, _load_ttl_map, _save_ttl_map


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


def rename_secret(
    vault_path: Path,
    passphrase: str,
    old_key: str,
    new_key: str,
    *,
    overwrite: bool = False,
) -> None:
    """Rename *old_key* to *new_key* inside the vault at *vault_path*.

    Tags and TTL entries associated with *old_key* are migrated to *new_key*.

    Parameters
    ----------
    vault_path:
        Path to the ``.vault`` file.
    passphrase:
        Passphrase used to decrypt / re-encrypt the vault.
    old_key:
        Existing secret key to rename.
    new_key:
        Target key name.
    overwrite:
        When ``True``, silently replace *new_key* if it already exists.
        Defaults to ``False``.

    Raises
    ------
    RenameError:
        If *old_key* does not exist, *new_key* already exists (and
        *overwrite* is ``False``), or the keys are identical.
    VaultError:
        Propagated from :class:`~envault.vault.Vault` on I/O or
        decryption failures.
    """
    if old_key == new_key:
        raise RenameError(f"Old and new key are identical: '{old_key}'")

    vault = Vault(vault_path, passphrase)
    secrets = vault.all()

    if old_key not in secrets:
        raise RenameError(f"Key not found in vault: '{old_key}'")

    if new_key in secrets and not overwrite:
        raise RenameError(
            f"Key '{new_key}' already exists. Use overwrite=True to replace it."
        )

    # Move the secret value.
    value = secrets[old_key]
    vault.delete(old_key)
    vault.set(new_key, value)

    # Migrate tags.
    tag_map = _load_tag_map(vault_path)
    if old_key in tag_map:
        tag_map.setdefault(new_key, set()).update(tag_map.pop(old_key))
        _save_tag_map(vault_path, tag_map)

    # Migrate TTL.
    ttl_map = _load_ttl_map(_ttl_path(vault_path))
    if old_key in ttl_map:
        ttl_map[new_key] = ttl_map.pop(old_key)
        _save_ttl_map(_ttl_path(vault_path), ttl_map)
