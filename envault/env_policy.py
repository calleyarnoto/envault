"""Secret policy enforcement — define and validate naming/value rules per-project."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import Vault, VaultError


class PolicyError(Exception):
    """Raised when a policy operation fails."""


@dataclass
class PolicyViolation:
    key: str
    rule: str
    message: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"PolicyViolation(key={self.key!r}, rule={self.rule!r}, message={self.message!r})"


def _policy_path(vault_path: Path) -> Path:
    return vault_path.parent / (vault_path.stem + ".policy.json")


def _load_policy(vault_path: Path) -> dict:
    p = _policy_path(vault_path)
    if not p.exists():
        return {}
    with p.open() as fh:
        return json.load(fh)


def _save_policy(vault_path: Path, data: dict) -> None:
    p = _policy_path(vault_path)
    with p.open("w") as fh:
        json.dump(data, fh, indent=2)


def set_policy(vault_path: Path, rule: str, value: str) -> None:
    """Set a policy rule (e.g. key_pattern, min_length, forbidden_prefix)."""
    allowed = {"key_pattern", "min_length", "max_length", "forbidden_prefix", "required_prefix"}
    if rule not in allowed:
        raise PolicyError(f"Unknown policy rule {rule!r}. Allowed: {sorted(allowed)}")
    if not vault_path.exists():
        raise PolicyError(f"Vault not found: {vault_path}")
    data = _load_policy(vault_path)
    data[rule] = value
    _save_policy(vault_path, data)


def get_policy(vault_path: Path) -> dict:
    """Return the current policy dict (may be empty)."""
    if not vault_path.exists():
        raise PolicyError(f"Vault not found: {vault_path}")
    return _load_policy(vault_path)


def check_policy(vault_path: Path, passphrase: str) -> List[PolicyViolation]:
    """Validate all secrets in the vault against the current policy."""
    if not vault_path.exists():
        raise PolicyError(f"Vault not found: {vault_path}")
    policy = _load_policy(vault_path)
    if not policy:
        return []
    vault = Vault(vault_path)
    try:
        secrets = vault.list_keys()
    except VaultError as exc:
        raise PolicyError(str(exc)) from exc

    violations: List[PolicyViolation] = []
    key_pattern = policy.get("key_pattern")
    min_length = int(policy["min_length"]) if "min_length" in policy else None
    max_length = int(policy["max_length"]) if "max_length" in policy else None
    forbidden_prefix = policy.get("forbidden_prefix")
    required_prefix = policy.get("required_prefix")

    for key in secrets:
        if key_pattern and not re.fullmatch(key_pattern, key):
            violations.append(PolicyViolation(key, "key_pattern",
                f"Key {key!r} does not match pattern {key_pattern!r}"))
        if forbidden_prefix and key.startswith(forbidden_prefix):
            violations.append(PolicyViolation(key, "forbidden_prefix",
                f"Key {key!r} starts with forbidden prefix {forbidden_prefix!r}"))
        if required_prefix and not key.startswith(required_prefix):
            violations.append(PolicyViolation(key, "required_prefix",
                f"Key {key!r} missing required prefix {required_prefix!r}"))
        value = vault.get(key, passphrase)
        if min_length is not None and len(value) < min_length:
            violations.append(PolicyViolation(key, "min_length",
                f"Value for {key!r} is shorter than minimum length {min_length}"))
        if max_length is not None and len(value) > max_length:
            violations.append(PolicyViolation(key, "max_length",
                f"Value for {key!r} exceeds maximum length {max_length}"))
    return violations
