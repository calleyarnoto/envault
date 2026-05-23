"""Secret reference resolution — allows values to reference other secrets via ${KEY} syntax."""

from __future__ import annotations

import re
from typing import Dict, List

from envault.vault import Vault, VaultError

_REF_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class RefError(Exception):
    """Raised when secret reference resolution fails."""


class RefResult:
    def __init__(self, key: str, resolved: str, refs: List[str]) -> None:
        self.key = key
        self.resolved = resolved
        self.refs = refs  # keys that were substituted

    def __repr__(self) -> str:  # pragma: no cover
        return f"RefResult(key={self.key!r}, refs={self.refs!r})"


def _find_refs(value: str) -> List[str]:
    """Return all ${KEY} reference names found in *value*."""
    return _REF_PATTERN.findall(value)


def resolve_refs(
    vault_path: str,
    passphrase: str,
    key: str,
    *,
    max_depth: int = 10,
) -> RefResult:
    """Resolve all ${KEY} references in the value stored under *key*.

    Raises RefError on circular references or missing keys.
    """
    if not vault_path or not passphrase:
        raise RefError("vault_path and passphrase are required")

    vault = Vault(vault_path)
    secrets: Dict[str, str] = vault.load(passphrase)

    if key not in secrets:
        raise RefError(f"Key not found: {key!r}")

    visited: List[str] = []

    def _resolve(value: str, depth: int) -> str:
        if depth > max_depth:
            raise RefError(f"Max reference depth ({max_depth}) exceeded — possible cycle")
        refs = _find_refs(value)
        for ref in refs:
            if ref not in secrets:
                raise RefError(f"Referenced key not found: {ref!r}")
            if ref in visited:
                raise RefError(f"Circular reference detected involving key: {ref!r}")
            visited.append(ref)
            replacement = _resolve(secrets[ref], depth + 1)
            value = value.replace(f"${{{ref}}}", replacement)
        return value

    resolved = _resolve(secrets[key], 0)
    return RefResult(key=key, resolved=resolved, refs=list(visited))


def resolve_all(
    vault_path: str,
    passphrase: str,
    *,
    max_depth: int = 10,
) -> Dict[str, RefResult]:
    """Resolve references for every key in the vault."""
    vault = Vault(vault_path)
    secrets: Dict[str, str] = vault.load(passphrase)
    return {
        k: resolve_refs(vault_path, passphrase, k, max_depth=max_depth)
        for k in secrets
    }
