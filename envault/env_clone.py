"""Clone secrets from one vault to another (or a new vault)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from envault.vault import Vault, VaultError


class CloneError(Exception):
    """Raised when a clone operation fails."""


def clone_vault(
    src_path: Path,
    src_passphrase: str,
    dst_path: Path,
    dst_passphrase: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> int:
    """Clone secrets from *src_path* into *dst_path*.

    Parameters
    ----------
    src_path:
        Path to the source vault file.
    src_passphrase:
        Passphrase for the source vault.
    dst_path:
        Path to the destination vault file.
    dst_passphrase:
        Passphrase for the destination vault (may differ from source).
    keys:
        Optional list of specific keys to clone.  If *None*, all keys are cloned.
    overwrite:
        When *True*, existing keys in the destination vault are overwritten.
        When *False* (default) existing keys are silently skipped.

    Returns
    -------
    int
        Number of secrets written to the destination vault.
    """
    if not src_path.exists():
        raise CloneError(f"Source vault not found: {src_path}")

    src = Vault(src_path, src_passphrase)
    try:
        src_secrets = src.list()  # {key: value}
    except VaultError as exc:
        raise CloneError(f"Cannot read source vault: {exc}") from exc

    # Resolve the set of keys to copy.
    if keys is not None:
        missing = [k for k in keys if k not in src_secrets]
        if missing:
            raise CloneError(f"Keys not found in source vault: {', '.join(missing)}")
        to_clone = {k: src_secrets[k] for k in keys}
    else:
        to_clone = dict(src_secrets)

    # Initialise destination vault if it does not yet exist.
    if not dst_path.exists():
        dst = Vault(dst_path, dst_passphrase)
        dst.init()
    else:
        dst = Vault(dst_path, dst_passphrase)
        try:
            dst.list()  # validate passphrase
        except VaultError as exc:
            raise CloneError(f"Cannot open destination vault: {exc}") from exc

    written = 0
    for key, value in to_clone.items():
        existing = dst.get(key)
        if existing is not None and not overwrite:
            continue
        dst.set(key, value)
        written += 1

    return written
