"""Tests for envault.env_schema."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_schema import (
    SchemaError,
    SchemaViolation,
    set_schema_rule,
    get_schema,
    validate_vault,
    _schema_path,
)

PASS = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vp = tmp_path / "test.vault"
    v = Vault(vp, PASS)
    v.init()
    v.set("API_KEY", "abc123")
    v.set("PORT", "8080")
    v.set("ENABLED", "true")
    v.set("EMAIL", "user@example.com")
    return vp


def test_set_schema_rule_persists(vault_file: Path) -> None:
    set_schema_rule(vault_file, "PORT", "type", "integer")
    schema = get_schema(vault_file)
    assert schema["PORT"]["type"] == "integer"


def test_set_multiple_rules_same_key(vault_file: Path) -> None:
    set_schema_rule(vault_file, "API_KEY", "min_length", "4")
    set_schema_rule(vault_file, "API_KEY", "max_length", "64")
    schema = get_schema(vault_file)
    assert schema["API_KEY"]["min_length"] == "4"
    assert schema["API_KEY"]["max_length"] == "64"


def test_set_unknown_rule_raises(vault_file: Path) -> None:
    with pytest.raises(SchemaError, match="Unknown rule"):
        set_schema_rule(vault_file, "PORT", "nonexistent", "foo")


def test_set_unknown_type_raises(vault_file: Path) -> None:
    with pytest.raises(SchemaError, match="Unknown type"):
        set_schema_rule(vault_file, "PORT", "type", "hexadecimal")


def test_set_schema_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(SchemaError, match="Vault not found"):
        set_schema_rule(tmp_path / "nope.vault", "KEY", "type", "string")


def test_get_schema_empty_when_no_file(vault_file: Path) -> None:
    assert get_schema(vault_file) == {}


def test_validate_no_schema_returns_empty(vault_file: Path) -> None:
    assert validate_vault(vault_file, PASS) == []


def test_validate_integer_type_passes(vault_file: Path) -> None:
    set_schema_rule(vault_file, "PORT", "type", "integer")
    violations = validate_vault(vault_file, PASS)
    assert not any(v.key == "PORT" for v in violations)


def test_validate_integer_type_fails(vault_file: Path) -> None:
    set_schema_rule(vault_file, "API_KEY", "type", "integer")
    violations = validate_vault(vault_file, PASS)
    assert any(v.key == "API_KEY" and v.rule == "type" for v in violations)


def test_validate_boolean_type_passes(vault_file: Path) -> None:
    set_schema_rule(vault_file, "ENABLED", "type", "boolean")
    assert validate_vault(vault_file, PASS) == []


def test_validate_email_type_passes(vault_file: Path) -> None:
    set_schema_rule(vault_file, "EMAIL", "type", "email")
    assert validate_vault(vault_file, PASS) == []


def test_validate_pattern_match(vault_file: Path) -> None:
    set_schema_rule(vault_file, "PORT", "pattern", r"^\d+$")
    assert validate_vault(vault_file, PASS) == []


def test_validate_pattern_mismatch(vault_file: Path) -> None:
    set_schema_rule(vault_file, "API_KEY", "pattern", r"^\d+$")
    violations = validate_vault(vault_file, PASS)
    assert any(v.key == "API_KEY" and v.rule == "pattern" for v in violations)


def test_schema_violation_has_message(vault_file: Path) -> None:
    set_schema_rule(vault_file, "API_KEY", "type", "integer")
    violations = validate_vault(vault_file, PASS)
    matching = [v for v in violations if v.key == "API_KEY" and v.rule == "type"]
    assert matching, "Expected a violation for API_KEY type rule"
    assert isinstance(matching[0].message, str)
    assert len(matching[0].message) > 0
