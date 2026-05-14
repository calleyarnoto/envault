"""Tests for envault.ttl — per-secret time-to-live support."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.ttl import (
    TTLError,
    expired_keys,
    get_ttl,
    purge_expired,
    remove_ttl,
    set_ttl,
)
from envault.vault import Vault

PASSPHRASE = "test-pass"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vp = tmp_path / "vault.env"
    v = Vault.init(vp, PASSPHRASE)
    v.set("DB_URL", "postgres://localhost/db")
    v.set("API_KEY", "secret123")
    v.set("TOKEN", "tok_abc")
    v.save()
    return vp


# ---------------------------------------------------------------------------
# set_ttl / get_ttl
# ---------------------------------------------------------------------------

def test_set_ttl_returns_future_timestamp(vault_file):
    before = time.time()
    expiry = set_ttl(vault_file, "DB_URL", 60)
    assert expiry > before + 59


def test_get_ttl_returns_none_when_not_set(vault_file):
    assert get_ttl(vault_file, "DB_URL") is None


def test_get_ttl_returns_expiry_after_set(vault_file):
    expiry = set_ttl(vault_file, "DB_URL", 120)
    assert get_ttl(vault_file, "DB_URL") == pytest.approx(expiry)


def test_set_ttl_zero_raises(vault_file):
    with pytest.raises(TTLError, match="positive"):
        set_ttl(vault_file, "DB_URL", 0)


def test_set_ttl_negative_raises(vault_file):
    with pytest.raises(TTLError, match="positive"):
        set_ttl(vault_file, "DB_URL", -10)


# ---------------------------------------------------------------------------
# remove_ttl
# ---------------------------------------------------------------------------

def test_remove_ttl_returns_true_when_existed(vault_file):
    set_ttl(vault_file, "API_KEY", 30)
    assert remove_ttl(vault_file, "API_KEY") is True


def test_remove_ttl_returns_false_when_missing(vault_file):
    assert remove_ttl(vault_file, "API_KEY") is False


def test_remove_ttl_clears_get_ttl(vault_file):
    set_ttl(vault_file, "TOKEN", 45)
    remove_ttl(vault_file, "TOKEN")
    assert get_ttl(vault_file, "TOKEN") is None


# ---------------------------------------------------------------------------
# expired_keys
# ---------------------------------------------------------------------------

def test_expired_keys_empty_when_no_ttls(vault_file):
    assert expired_keys(vault_file) == []


def test_expired_keys_not_yet_expired(vault_file):
    set_ttl(vault_file, "DB_URL", 9999)
    assert "DB_URL" not in expired_keys(vault_file)


def test_expired_keys_detects_past_expiry(vault_file):
    set_ttl(vault_file, "API_KEY", 0.001)
    time.sleep(0.01)
    assert "API_KEY" in expired_keys(vault_file)


# ---------------------------------------------------------------------------
# purge_expired
# ---------------------------------------------------------------------------

def test_purge_expired_removes_keys_from_vault(vault_file):
    set_ttl(vault_file, "TOKEN", 0.001)
    time.sleep(0.01)
    removed = purge_expired(vault_file, PASSPHRASE)
    assert "TOKEN" in removed
    v = Vault.load(vault_file, PASSPHRASE)
    assert "TOKEN" not in v.list_keys()


def test_purge_expired_returns_empty_when_nothing_expired(vault_file):
    set_ttl(vault_file, "DB_URL", 9999)
    assert purge_expired(vault_file, PASSPHRASE) == []


def test_purge_expired_clears_ttl_entry(vault_file):
    set_ttl(vault_file, "API_KEY", 0.001)
    time.sleep(0.01)
    purge_expired(vault_file, PASSPHRASE)
    assert get_ttl(vault_file, "API_KEY") is None
