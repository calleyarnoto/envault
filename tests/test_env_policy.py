"""Tests for envault.env_policy."""
import json
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_policy import (
    PolicyError,
    PolicyViolation,
    set_policy,
    get_policy,
    check_policy,
    _policy_path,
)

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path):
    vp = tmp_path / "test.vault"
    v = Vault(vp)
    v.init(PASS)
    v.set("APP_KEY", "secret123", PASS)
    v.set("APP_TOKEN", "x" * 5, PASS)
    v.set("DEBUG", "true", PASS)
    return vp


# --- set_policy / get_policy ---

def test_set_policy_persists(vault_file):
    set_policy(vault_file, "key_pattern", "[A-Z_]+")
    data = get_policy(vault_file)
    assert data["key_pattern"] == "[A-Z_]+"


def test_set_multiple_rules(vault_file):
    set_policy(vault_file, "min_length", "4")
    set_policy(vault_file, "max_length", "50")
    data = get_policy(vault_file)
    assert data["min_length"] == "4"
    assert data["max_length"] == "50"


def test_set_unknown_rule_raises(vault_file):
    with pytest.raises(PolicyError, match="Unknown policy rule"):
        set_policy(vault_file, "nonexistent_rule", "value")


def test_set_policy_missing_vault_raises(tmp_path):
    with pytest.raises(PolicyError, match="Vault not found"):
        set_policy(tmp_path / "missing.vault", "min_length", "8")


def test_get_policy_empty_when_no_file(vault_file):
    data = get_policy(vault_file)
    assert data == {}


def test_get_policy_missing_vault_raises(tmp_path):
    with pytest.raises(PolicyError, match="Vault not found"):
        get_policy(tmp_path / "missing.vault")


# --- check_policy ---

def test_check_policy_no_policy_returns_empty(vault_file):
    violations = check_policy(vault_file, PASS)
    assert violations == []


def test_check_key_pattern_violation(vault_file):
    set_policy(vault_file, "key_pattern", "APP_[A-Z]+")
    violations = check_policy(vault_file, PASS)
    keys = [v.key for v in violations]
    assert "DEBUG" in keys
    assert all(v.rule == "key_pattern" for v in violations if v.key == "DEBUG")


def test_check_key_pattern_all_pass(vault_file):
    set_policy(vault_file, "key_pattern", "[A-Z_]+")
    violations = check_policy(vault_file, PASS)
    assert violations == []


def test_check_min_length_violation(vault_file):
    set_policy(vault_file, "min_length", "6")
    violations = check_policy(vault_file, PASS)
    keys = [v.key for v in violations]
    assert "APP_TOKEN" in keys  # value is 5 chars
    assert "DEBUG" in keys      # value is 4 chars


def test_check_max_length_violation(vault_file):
    set_policy(vault_file, "max_length", "4")
    violations = check_policy(vault_file, PASS)
    keys = [v.key for v in violations]
    assert "APP_KEY" in keys    # 9 chars
    assert "APP_TOKEN" in keys  # 5 chars


def test_check_required_prefix_violation(vault_file):
    set_policy(vault_file, "required_prefix", "APP_")
    violations = check_policy(vault_file, PASS)
    keys = [v.key for v in violations]
    assert "DEBUG" in keys
    assert "APP_KEY" not in keys


def test_check_forbidden_prefix_violation(vault_file):
    set_policy(vault_file, "forbidden_prefix", "APP_")
    violations = check_policy(vault_file, PASS)
    keys = [v.key for v in violations]
    assert "APP_KEY" in keys
    assert "APP_TOKEN" in keys
    assert "DEBUG" not in keys


def test_violation_repr(vault_file):
    v = PolicyViolation("MY_KEY", "min_length", "too short")
    assert "MY_KEY" in repr(v)
    assert "min_length" in repr(v)


def test_check_policy_missing_vault_raises(tmp_path):
    with pytest.raises(PolicyError, match="Vault not found"):
        check_policy(tmp_path / "missing.vault", PASS)
