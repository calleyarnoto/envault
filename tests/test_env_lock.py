"""Tests for envault/env_lock.py."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault.env_lock import (
    LockError,
    is_locked,
    lock_status,
    lock_vault,
    unlock_vault,
)

PASSPHRASE = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "vault.json"
    vf.write_text('{"secrets":{}}', encoding="utf-8")
    return vf


def test_lock_vault_creates_lock_file(vault_file):
    lock_file = lock_vault(vault_file, PASSPHRASE)
    assert lock_file.exists()


def test_lock_vault_returns_lock_path(vault_file):
    lock_file = lock_vault(vault_file, PASSPHRASE)
    assert lock_file.name == ".envault_lock"
    assert lock_file.parent == vault_file.parent


def test_lock_vault_payload_contains_expected_keys(vault_file):
    lock_file = lock_vault(vault_file, PASSPHRASE)
    payload = json.loads(lock_file.read_text())
    assert "token" in payload
    assert "expires_at" in payload
    assert "vault" in payload


def test_lock_vault_custom_ttl(vault_file):
    lock_file = lock_vault(vault_file, PASSPHRASE, ttl=120)
    payload = json.loads(lock_file.read_text())
    assert payload["expires_at"] == pytest.approx(time.time() + 120, abs=2)


def test_lock_vault_zero_ttl_raises(vault_file):
    with pytest.raises(LockError, match="positive"):
        lock_vault(vault_file, PASSPHRASE, ttl=0)


def test_lock_vault_missing_vault_raises(tmp_path):
    with pytest.raises(LockError, match="not found"):
        lock_vault(tmp_path / "nonexistent.json", PASSPHRASE)


def test_is_locked_true_after_lock(vault_file):
    lock_vault(vault_file, PASSPHRASE)
    assert is_locked(vault_file, PASSPHRASE) is True


def test_is_locked_false_wrong_passphrase(vault_file):
    lock_vault(vault_file, PASSPHRASE)
    assert is_locked(vault_file, "wrongpass") is False


def test_is_locked_false_when_no_lock_file(vault_file):
    assert is_locked(vault_file, PASSPHRASE) is False


def test_is_locked_false_after_expiry(vault_file, tmp_path):
    lock_file = lock_vault(vault_file, PASSPHRASE, ttl=1)
    # Manually backdate expiry
    payload = json.loads(lock_file.read_text())
    payload["expires_at"] = time.time() - 10
    lock_file.write_text(json.dumps(payload))
    assert is_locked(vault_file, PASSPHRASE) is False
    assert not lock_file.exists()  # should be cleaned up


def test_unlock_removes_lock_file(vault_file):
    lock_vault(vault_file, PASSPHRASE)
    unlock_vault(vault_file)
    assert not (vault_file.parent / ".envault_lock").exists()


def test_unlock_no_op_when_not_locked(vault_file):
    # Should not raise even if no lock file exists
    unlock_vault(vault_file)


def test_lock_status_locked(vault_file):
    lock_vault(vault_file, PASSPHRASE, ttl=300)
    status = lock_status(vault_file)
    assert status["locked"] is True
    assert status["remaining_seconds"] > 0


def test_lock_status_not_locked(vault_file):
    status = lock_status(vault_file)
    assert status == {"locked": False}
