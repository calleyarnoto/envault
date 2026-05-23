"""Tests for envault.env_pin."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_pin import (
    PinError,
    pin_secret,
    unpin_secret,
    list_pins,
    check_pins,
)

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vp = tmp_path / "test.vault"
    v = Vault(vp, PASS)
    v.init()
    v.set("API_KEY", "abc123")
    v.set("DB_PASS", "secret")
    v.set("TOKEN", "tok_xyz")
    return vp


def test_pin_returns_current_value(vault_file):
    val = pin_secret(vault_file, PASS, "API_KEY")
    assert val == "abc123"


def test_pin_appears_in_list(vault_file):
    pin_secret(vault_file, PASS, "API_KEY")
    assert "API_KEY" in list_pins(vault_file)


def test_list_pins_empty_when_no_pins(vault_file):
    assert list_pins(vault_file) == []


def test_list_pins_sorted(vault_file):
    pin_secret(vault_file, PASS, "TOKEN")
    pin_secret(vault_file, PASS, "API_KEY")
    assert list_pins(vault_file) == ["API_KEY", "TOKEN"]


def test_pin_idempotent(vault_file):
    pin_secret(vault_file, PASS, "API_KEY")
    pin_secret(vault_file, PASS, "API_KEY")
    assert list_pins(vault_file).count("API_KEY") == 1


def test_pin_missing_key_raises(vault_file):
    with pytest.raises(PinError, match="not found"):
        pin_secret(vault_file, PASS, "NONEXISTENT")


def test_pin_missing_vault_raises(tmp_path):
    with pytest.raises(PinError, match="Vault not found"):
        pin_secret(tmp_path / "ghost.vault", PASS, "KEY")


def test_unpin_removes_key(vault_file):
    pin_secret(vault_file, PASS, "DB_PASS")
    unpin_secret(vault_file, "DB_PASS")
    assert "DB_PASS" not in list_pins(vault_file)


def test_unpin_not_pinned_raises(vault_file):
    with pytest.raises(PinError, match="not pinned"):
        unpin_secret(vault_file, "API_KEY")


def test_check_pins_match(vault_file):
    pin_secret(vault_file, PASS, "API_KEY")
    results = check_pins(vault_file, PASS)
    assert results["API_KEY"] is True


def test_check_pins_detects_drift(vault_file):
    pin_secret(vault_file, PASS, "API_KEY")
    v = Vault(vault_file, PASS)
    v.set("API_KEY", "new_value")
    results = check_pins(vault_file, PASS)
    assert results["API_KEY"] is False


def test_check_pins_empty_when_no_pins(vault_file):
    assert check_pins(vault_file, PASS) == {}


def test_check_pins_missing_vault_raises(tmp_path):
    with pytest.raises(PinError, match="Vault not found"):
        check_pins(tmp_path / "ghost.vault", PASS)
