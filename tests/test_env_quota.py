"""Tests for envault.env_quota."""
from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.env_quota import (
    QuotaError,
    set_quota,
    get_quota,
    check_quota,
    enforce_quota,
    clear_quota,
    _quota_path,
)

PASS = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "secrets.vault"
    Vault(p, PASS).init()
    return p


def _add(vault_file, key, value):
    v = Vault(vault_file, PASS)
    v.set(key, value)


# --- set_quota ---

def test_set_quota_returns_max(vault_file):
    assert set_quota(vault_file, 10) == 10


def test_set_quota_persists(vault_file):
    set_quota(vault_file, 5)
    assert get_quota(vault_file) == 5


def test_set_quota_zero_raises(vault_file):
    with pytest.raises(QuotaError, match="at least 1"):
        set_quota(vault_file, 0)


def test_set_quota_missing_vault_raises(tmp_path):
    with pytest.raises(QuotaError, match="not found"):
        set_quota(tmp_path / "missing.vault", 10)


def test_set_quota_creates_quota_file(vault_file):
    set_quota(vault_file, 20)
    assert _quota_path(vault_file).exists()


# --- get_quota ---

def test_get_quota_returns_none_when_not_set(vault_file):
    assert get_quota(vault_file) is None


def test_get_quota_returns_value_after_set(vault_file):
    set_quota(vault_file, 7)
    assert get_quota(vault_file) == 7


# --- check_quota ---

def test_check_quota_current_count(vault_file):
    _add(vault_file, "KEY1", "val1")
    _add(vault_file, "KEY2", "val2")
    result = check_quota(vault_file, PASS)
    assert result["current"] == 2


def test_check_quota_at_limit_false(vault_file):
    set_quota(vault_file, 5)
    _add(vault_file, "A", "1")
    result = check_quota(vault_file, PASS)
    assert result["at_limit"] is False


def test_check_quota_at_limit_true(vault_file):
    set_quota(vault_file, 1)
    _add(vault_file, "A", "1")
    result = check_quota(vault_file, PASS)
    assert result["at_limit"] is True


def test_check_quota_no_limit_never_at_limit(vault_file):
    for i in range(5):
        _add(vault_file, f"K{i}", str(i))
    result = check_quota(vault_file, PASS)
    assert result["limit"] is None
    assert result["at_limit"] is False


# --- enforce_quota ---

def test_enforce_quota_raises_when_at_limit(vault_file):
    set_quota(vault_file, 1)
    _add(vault_file, "X", "y")
    with pytest.raises(QuotaError, match="Quota reached"):
        enforce_quota(vault_file, PASS)


def test_enforce_quota_passes_when_under_limit(vault_file):
    set_quota(vault_file, 10)
    _add(vault_file, "X", "y")
    enforce_quota(vault_file, PASS)  # should not raise


# --- clear_quota ---

def test_clear_quota_removes_file(vault_file):
    set_quota(vault_file, 5)
    clear_quota(vault_file)
    assert not _quota_path(vault_file).exists()


def test_clear_quota_idempotent(vault_file):
    clear_quota(vault_file)  # no file exists — should not raise


def test_clear_quota_resets_get_to_none(vault_file):
    set_quota(vault_file, 3)
    clear_quota(vault_file)
    assert get_quota(vault_file) is None
