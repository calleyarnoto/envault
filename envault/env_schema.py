"""Schema validation for vault secrets — enforce types, patterns, and required keys."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from envault.vault import Vault, VaultError


class SchemaError(Exception):
    """Raised for schema definition or validation failures."""


@dataclass
class SchemaViolation:
    key: str
    rule: str
    message: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"SchemaViolation(key={self.key!r}, rule={self.rule!r}, message={self.message!r})"


_VALID_TYPES = {"string", "integer", "boolean", "url", "email"}
_TYPE_PATTERNS: dict[str, re.Pattern[str]] = {
    "integer": re.compile(r"^-?\d+$"),
    "boolean": re.compile(r"^(true|false|1|0|yes|no)$", re.IGNORECASE),
    "url": re.compile(r"^https?://[^\s]+$"),
    "email": re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
}


def _schema_path(vault_path: Path) -> Path:
    return vault_path.parent / (vault_path.stem + ".schema.json")


def _load_schema(vault_path: Path) -> dict[str, Any]:
    sp = _schema_path(vault_path)
    if not sp.exists():
        return {}
    return json.loads(sp.read_text())


def _save_schema(vault_path: Path, schema: dict[str, Any]) -> None:
    _schema_path(vault_path).write_text(json.dumps(schema, indent=2))


def set_schema_rule(vault_path: Path, key: str, rule: str, value: str) -> None:
    """Define a validation rule for a secret key."""
    if not vault_path.exists():
        raise SchemaError(f"Vault not found: {vault_path}")
    allowed_rules = {"type", "pattern", "required", "min_length", "max_length"}
    if rule not in allowed_rules:
        raise SchemaError(f"Unknown rule {rule!r}. Allowed: {sorted(allowed_rules)}")
    if rule == "type" and value not in _VALID_TYPES:
        raise SchemaError(f"Unknown type {value!r}. Allowed: {sorted(_VALID_TYPES)}")
    schema = _load_schema(vault_path)
    schema.setdefault(key, {})[rule] = value
    _save_schema(vault_path, schema)


def get_schema(vault_path: Path) -> dict[str, Any]:
    """Return the full schema definition for the vault."""
    return _load_schema(vault_path)


def validate_vault(vault_path: Path, passphrase: str) -> list[SchemaViolation]:
    """Validate all vault secrets against the defined schema."""
    if not vault_path.exists():
        raise SchemaError(f"Vault not found: {vault_path}")
    schema = _load_schema(vault_path)
    if not schema:
        return []
    vault = Vault(vault_path, passphrase)
    secrets = vault.list()
    violations: list[SchemaViolation] = []

    for key, rules in schema.items():
        required = rules.get("required", "false").lower() in ("true", "1", "yes")
        if key not in secrets:
            if required:
                violations.append(SchemaViolation(key, "required", f"Key {key!r} is required but missing"))
            continue
        value = vault.get(key)
        if "type" in rules:
            t = rules["type"]
            pat = _TYPE_PATTERNS.get(t)
            if pat and not pat.match(value):
                violations.append(SchemaViolation(key, "type", f"Value does not match type {t!r}"))
        if "pattern" in rules:
            if not re.search(rules["pattern"], value):
                violations.append(SchemaViolation(key, "pattern", f"Value does not match pattern {rules['pattern']!r}"))
        if "min_length" in rules:
            ml = int(rules["min_length"])
            if len(value) < ml:
                violations.append(SchemaViolation(key, "min_length", f"Value length {len(value)} < min_length {ml}"))
        if "max_length" in rules:
            ml = int(rules["max_length"])
            if len(value) > ml:
                violations.append(SchemaViolation(key, "max_length", f"Value length {len(value)} > max_length {ml}"))
    return violations
