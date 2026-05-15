"""Merge secrets from multiple vaults into a target vault."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class MergeError(Exception):
    """Raised when a merge operation fails."""


@dataclass
class MergeResult:
    added: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.overwritten)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.overwritten:
            parts.append(f"{len(self.overwritten)} overwritten")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        return ", ".join(parts) if parts else "nothing changed"


def merge_vaults(
    src_path: str,
    src_passphrase: str,
    dst_path: str,
    dst_passphrase: str,
    *,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> MergeResult:
    """Merge secrets from *src* vault into *dst* vault.

    Args:
        src_path: Path to the source vault file.
        src_passphrase: Passphrase for the source vault.
        dst_path: Path to the destination vault file.
        dst_passphrase: Passphrase for the destination vault.
        keys: Optional list of keys to merge; merges all keys when ``None``.
        overwrite: When ``True``, existing keys in the destination are
            overwritten; otherwise they are skipped.

    Returns:
        A :class:`MergeResult` describing what happened.

    Raises:
        MergeError: If either vault cannot be opened or a requested key is
            missing from the source.
    """
    try:
        src = Vault.load(src_path, src_passphrase)
    except VaultError as exc:
        raise MergeError(f"Cannot open source vault: {exc}") from exc

    try:
        dst = Vault.load(dst_path, dst_passphrase)
    except VaultError as exc:
        raise MergeError(f"Cannot open destination vault: {exc}") from exc

    src_secrets: Dict[str, str] = src.list()
    dst_secrets: Dict[str, str] = dst.list()

    candidates = keys if keys is not None else list(src_secrets.keys())

    missing = [k for k in candidates if k not in src_secrets]
    if missing:
        raise MergeError(f"Keys not found in source vault: {', '.join(sorted(missing))}")

    result = MergeResult()

    for key in sorted(candidates):
        value = src_secrets[key]
        if key in dst_secrets:
            if overwrite:
                dst.set(key, value)
                result.overwritten.append(key)
            else:
                result.skipped.append(key)
        else:
            dst.set(key, value)
            result.added.append(key)

    dst.save()
    return result
