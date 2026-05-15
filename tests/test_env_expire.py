"""Tests for envault.env_expire."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.vault import Vault
from envault.env_expire import (
    ExpireError,
    get_expiry,
    list_expired,
    purge_expired,
    set_expiry,
)

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "vault.env"
    v = Vault(p)
    v.init(PASS)
    v.set("API_KEY", "abc123", PASS)
    v.set("DB_PASS", "secret", PASS)
    return p


def test_set_expiry_returns_future_timestamp(vault_file):
    before = time.time()
    ts = set_expiry(vault_file, "API_KEY", days=7, passphrase=PASS)
    assert ts > before + 6 * 86400


def test_get_expiry_returns_none_when_not_set(vault_file):
    assert get_expiry(vault_file, "API_KEY") is None


def test_get_expiry_returns_timestamp_after_set(vault_file):
    ts = set_expiry(vault_file, "API_KEY", days=1, passphrase=PASS)
    assert get_expiry(vault_file, "API_KEY") == pytest.approx(ts)


def test_set_expiry_zero_days_raises(vault_file):
    with pytest.raises(ExpireError, match="positive"):
        set_expiry(vault_file, "API_KEY", days=0, passphrase=PASS)


def test_set_expiry_negative_days_raises(vault_file):
    with pytest.raises(ExpireError, match="positive"):
        set_expiry(vault_file, "API_KEY", days=-3, passphrase=PASS)


def test_set_expiry_missing_key_raises(vault_file):
    with pytest.raises(ExpireError, match="not found"):
        set_expiry(vault_file, "NONEXISTENT", days=1, passphrase=PASS)


def test_list_expired_empty_when_none_set(vault_file):
    assert list_expired(vault_file, PASS) == []


def test_list_expired_returns_past_keys(vault_file, monkeypatch):
    set_expiry(vault_file, "API_KEY", days=1, passphrase=PASS)
    # Wind time forward past expiry
    monkeypatch.setattr("envault.env_expire.time.time", lambda: time.time() + 2 * 86400)
    expired = list_expired(vault_file, PASS)
    keys = [k for k, _ in expired]
    assert "API_KEY" in keys


def test_list_expired_excludes_future_keys(vault_file):
    set_expiry(vault_file, "API_KEY", days=30, passphrase=PASS)
    assert list_expired(vault_file, PASS) == []


def test_purge_expired_removes_secrets(vault_file, monkeypatch):
    set_expiry(vault_file, "API_KEY", days=1, passphrase=PASS)
    monkeypatch.setattr("envault.env_expire.time.time", lambda: time.time() + 2 * 86400)
    purged = purge_expired(vault_file, PASS)
    assert "API_KEY" in purged
    v = Vault(vault_file)
    v.load(PASS)
    assert "API_KEY" not in v.secrets


def test_purge_expired_clears_expiry_map(vault_file, monkeypatch):
    set_expiry(vault_file, "API_KEY", days=1, passphrase=PASS)
    monkeypatch.setattr("envault.env_expire.time.time", lambda: time.time() + 2 * 86400)
    purge_expired(vault_file, PASS)
    assert get_expiry(vault_file, "API_KEY") is None


def test_purge_expired_returns_empty_when_nothing_expired(vault_file):
    set_expiry(vault_file, "API_KEY", days=30, passphrase=PASS)
    assert purge_expired(vault_file, PASS) == []
