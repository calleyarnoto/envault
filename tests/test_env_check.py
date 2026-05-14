"""Tests for envault.env_check."""

from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.env_check import CheckError, CheckResult, check_secrets


PASS = "hunter2"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(tmp_path / "vault.json")
    v.init(PASS)
    return v


# ---------------------------------------------------------------------------
# Basic result structure
# ---------------------------------------------------------------------------

def test_returns_empty_list_when_all_ok(vault):
    vault.set("DATABASE_URL", "https://db.example.com", PASS)
    results = check_secrets(vault, PASS)
    assert results == []


def test_check_result_repr():
    r = CheckResult(key="FOO", status="missing", message="not found")
    assert "FOO" in repr(r)
    assert "missing" in repr(r)


# ---------------------------------------------------------------------------
# Required-key checks
# ---------------------------------------------------------------------------

def test_missing_required_key_reported(vault):
    results = check_secrets(vault, PASS, required_keys=["MUST_EXIST"])
    assert len(results) == 1
    assert results[0].key == "MUST_EXIST"
    assert results[0].status == "missing"


def test_present_required_key_not_reported(vault):
    vault.set("MUST_EXIST", "yes", PASS)
    results = check_secrets(vault, PASS, required_keys=["MUST_EXIST"])
    assert results == []


def test_multiple_missing_keys_all_reported(vault):
    results = check_secrets(vault, PASS, required_keys=["A", "B", "C"])
    missing = {r.key for r in results}
    assert missing == {"A", "B", "C"}


# ---------------------------------------------------------------------------
# Format checks
# ---------------------------------------------------------------------------

def test_url_key_with_valid_value_passes(vault):
    vault.set("API_URL", "https://api.example.com", PASS)
    results = check_secrets(vault, PASS)
    assert results == []


def test_url_key_with_invalid_value_flagged(vault):
    vault.set("API_URL", "not-a-url", PASS)
    results = check_secrets(vault, PASS)
    assert len(results) == 1
    assert results[0].status == "invalid_format"
    assert results[0].key == "API_URL"


def test_email_key_with_valid_value_passes(vault):
    vault.set("ADMIN_EMAIL", "admin@example.com", PASS)
    results = check_secrets(vault, PASS)
    assert results == []


def test_email_key_with_invalid_value_flagged(vault):
    vault.set("ADMIN_EMAIL", "not-an-email", PASS)
    results = check_secrets(vault, PASS)
    assert any(r.key == "ADMIN_EMAIL" and r.status == "invalid_format" for r in results)


def test_port_key_with_valid_value_passes(vault):
    vault.set("DB_PORT", "5432", PASS)
    results = check_secrets(vault, PASS)
    assert results == []


def test_port_key_with_invalid_value_flagged(vault):
    vault.set("DB_PORT", "not-a-port", PASS)
    results = check_secrets(vault, PASS)
    assert any(r.key == "DB_PORT" and r.status == "invalid_format" for r in results)


def test_format_check_disabled(vault):
    vault.set("API_URL", "not-a-url", PASS)
    results = check_secrets(vault, PASS, check_format=False)
    assert results == []


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_check_error_raised_for_missing_vault(tmp_path):
    v = Vault(tmp_path / "nonexistent.json")
    with pytest.raises(CheckError):
        check_secrets(v, PASS)
