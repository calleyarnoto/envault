"""Tests for envault.rotate."""

from __future__ import annotations

import pytest

from envault.audit import AuditLog
from envault.rotate import RotationError, rotate_passphrase
from envault.vault import Vault


OLD_PASS = "old-secret-pass"
NEW_PASS = "new-secret-pass"


@pytest.fixture()
def populated_vault(tmp_path):
    path = tmp_path / "vault.json"
    v = Vault(path, OLD_PASS)
    v.init()
    v.set("KEY_A", "alpha")
    v.set("KEY_B", "beta")
    return path


def test_rotate_returns_secret_count(populated_vault):
    count = rotate_passphrase(populated_vault, OLD_PASS, NEW_PASS)
    assert count == 2


def test_rotate_new_passphrase_can_decrypt(populated_vault):
    rotate_passphrase(populated_vault, OLD_PASS, NEW_PASS)
    v = Vault(populated_vault, NEW_PASS)
    v.load()
    assert v.get("KEY_A") == "alpha"
    assert v.get("KEY_B") == "beta"


def test_rotate_old_passphrase_no_longer_works(populated_vault):
    rotate_passphrase(populated_vault, OLD_PASS, NEW_PASS)
    v = Vault(populated_vault, OLD_PASS)
    with pytest.raises(Exception):
        v.load()


def test_rotate_raises_if_vault_missing(tmp_path):
    missing = tmp_path / "no_vault.json"
    with pytest.raises(RotationError, match="Vault not found"):
        rotate_passphrase(missing, OLD_PASS, NEW_PASS)


def test_rotate_raises_if_same_passphrase(populated_vault):
    with pytest.raises(RotationError, match="must differ"):
        rotate_passphrase(populated_vault, OLD_PASS, OLD_PASS)


def test_rotate_raises_on_wrong_old_passphrase(populated_vault):
    with pytest.raises(RotationError, match="Could not open vault"):
        rotate_passphrase(populated_vault, "wrong-pass", NEW_PASS)


def test_rotate_writes_audit_entry(populated_vault, tmp_path):
    log_path = tmp_path / "audit.log"
    log = AuditLog(log_path)
    rotate_passphrase(populated_vault, OLD_PASS, NEW_PASS, audit_log=log, actor="tester")
    entries = log.load()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.action == "rotate"
    assert entry.actor == "tester"
    assert entry.metadata["secrets_rotated"] == 2


def test_rotate_empty_vault(tmp_path):
    path = tmp_path / "empty.json"
    v = Vault(path, OLD_PASS)
    v.init()
    count = rotate_passphrase(path, OLD_PASS, NEW_PASS)
    assert count == 0
