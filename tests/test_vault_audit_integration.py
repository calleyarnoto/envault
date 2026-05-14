"""Integration tests verifying that Vault operations emit audit log entries."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.audit import AUDIT_LOG_FILENAME, load_audit_log
from envault.vault import Vault, VaultError

PASS = "integration-passphrase-42"


@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    vp = tmp_path / "test.vault"
    return Vault.init(vp, PASS)


def _log(vault: Vault) -> list:
    return load_audit_log(vault._path)


def test_init_creates_audit_entry(vault: Vault):
    entries = _log(vault)
    assert len(entries) == 1
    assert entries[0].action == "init"


def test_set_appends_audit_entry(vault: Vault):
    vault.set("MY_KEY", "my_value")
    entries = _log(vault)
    actions = [e.action for e in entries]
    assert "set" in actions
    set_entry = next(e for e in entries if e.action == "set")
    assert set_entry.key == "MY_KEY"


def test_get_appends_audit_entry(vault: Vault):
    vault.set("TOKEN", "abc123")
    vault.get("TOKEN")
    entries = _log(vault)
    get_entries = [e for e in entries if e.action == "get"]
    assert len(get_entries) == 1
    assert get_entries[0].key == "TOKEN"


def test_delete_appends_audit_entry(vault: Vault):
    vault.set("OLD_KEY", "val")
    vault.delete("OLD_KEY")
    entries = _log(vault)
    delete_entries = [e for e in entries if e.action == "delete"]
    assert len(delete_entries) == 1
    assert delete_entries[0].key == "OLD_KEY"


def test_audit_log_accumulates_across_operations(vault: Vault):
    vault.set("A", "1")
    vault.set("B", "2")
    vault.get("A")
    vault.delete("B")
    entries = _log(vault)
    # init + set + set + get + delete = 5
    assert len(entries) == 5


def test_audit_log_survives_vault_reload(tmp_path: Path):
    vp = tmp_path / "reload.vault"
    v1 = Vault.init(vp, PASS)
    v1.set("RELOAD_KEY", "value")

    v2 = Vault.load(vp, PASS)
    v2.get("RELOAD_KEY")

    entries = load_audit_log(vp)
    actions = [e.action for e in entries]
    assert actions == ["init", "set", "get"]


def test_audit_log_not_inside_encrypted_vault(vault: Vault):
    """Audit log must be a separate plaintext file, not embedded in the vault."""
    log_path = vault._path.parent / AUDIT_LOG_FILENAME
    assert log_path.exists()
    # The vault file itself should not contain the word 'audit'
    vault_content = vault._path.read_text()
    assert "audit" not in vault_content
