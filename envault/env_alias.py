"""Secret aliasing: create human-friendly aliases that point to vault keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault, VaultError


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _alias_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".aliases.json")


def _load_aliases(vault_path: Path) -> Dict[str, str]:
    p = _alias_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_aliases(vault_path: Path, aliases: Dict[str, str]) -> None:
    _alias_path(vault_path).write_text(json.dumps(aliases, indent=2, sort_keys=True))


def add_alias(vault_path: Path, alias: str, target_key: str, passphrase: str) -> str:
    """Create *alias* pointing to *target_key*. Returns the resolved value."""
    if not alias or not alias.strip():
        raise AliasError("Alias name must not be empty.")
    vault = Vault(vault_path, passphrase)
    secrets = vault.list()
    if target_key not in secrets:
        raise AliasError(f"Target key '{target_key}' does not exist in vault.")
    aliases = _load_aliases(vault_path)
    if alias == target_key:
        raise AliasError("Alias name must differ from the target key.")
    aliases[alias] = target_key
    _save_aliases(vault_path, aliases)
    return vault.get(target_key)


def remove_alias(vault_path: Path, alias: str) -> None:
    """Delete an existing alias."""
    aliases = _load_aliases(vault_path)
    if alias not in aliases:
        raise AliasError(f"Alias '{alias}' not found.")
    del aliases[alias]
    _save_aliases(vault_path, aliases)


def resolve_alias(vault_path: Path, alias: str, passphrase: str) -> str:
    """Return the value of the key that *alias* points to."""
    aliases = _load_aliases(vault_path)
    if alias not in aliases:
        raise AliasError(f"Alias '{alias}' not found.")
    target = aliases[alias]
    vault = Vault(vault_path, passphrase)
    return vault.get(target)


def list_aliases(vault_path: Path) -> List[Dict[str, str]]:
    """Return sorted list of {alias, target} dicts."""
    aliases = _load_aliases(vault_path)
    return [{"alias": a, "target": t} for a, t in sorted(aliases.items())]
