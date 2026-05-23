"""Tests for envault.env_access."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.env_access import (
    AccessError,
    grant_access,
    revoke_access,
    list_access,
    can_access,
    _access_path,
)
from envault.vault import Vault


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vp = tmp_path / "vault.env"
    v = Vault(vp)
    v.init("passphrase")
    v.set("DB_HOST", "localhost", "passphrase")
    v.set("DB_PASS", "secret", "passphrase")
    v.set("API_KEY", "abc123", "passphrase")
    return vp


# --- grant_access ---

def test_grant_access_returns_count(vault_file):
    n = grant_access(vault_file, "ci", ["DB_HOST", "API_KEY"])
    assert n == 2


def test_grant_access_creates_access_file(vault_file):
    grant_access(vault_file, "ci", ["DB_HOST"])
    assert _access_path(vault_file).exists()


def test_grant_access_idempotent(vault_file):
    grant_access(vault_file, "ci", ["DB_HOST"])
    n = grant_access(vault_file, "ci", ["DB_HOST"])
    assert n == 0


def test_grant_access_write_permission(vault_file):
    grant_access(vault_file, "admin", ["DB_PASS"], permission="write")
    assert can_access(vault_file, "admin", "DB_PASS", "write")


def test_grant_access_missing_vault_raises(tmp_path):
    with pytest.raises(AccessError, match="Vault not found"):
        grant_access(tmp_path / "missing.env", "ci", ["KEY"])


def test_grant_access_empty_role_raises(vault_file):
    with pytest.raises(AccessError, match="Role must not be empty"):
        grant_access(vault_file, "  ", ["DB_HOST"])


def test_grant_access_invalid_permission_raises(vault_file):
    with pytest.raises(AccessError, match="Invalid permission"):
        grant_access(vault_file, "ci", ["DB_HOST"], permission="execute")


def test_grant_access_no_keys_raises(vault_file):
    with pytest.raises(AccessError, match="At least one key"):
        grant_access(vault_file, "ci", [])


# --- revoke_access ---

def test_revoke_access_returns_count(vault_file):
    grant_access(vault_file, "ci", ["DB_HOST", "API_KEY"])
    n = revoke_access(vault_file, "ci", ["API_KEY"])
    assert n == 1


def test_revoke_access_removes_key(vault_file):
    grant_access(vault_file, "ci", ["DB_HOST"])
    revoke_access(vault_file, "ci", ["DB_HOST"])
    assert not can_access(vault_file, "ci", "DB_HOST")


def test_revoke_access_unknown_role_returns_zero(vault_file):
    n = revoke_access(vault_file, "ghost", ["DB_HOST"])
    assert n == 0


def test_revoke_access_invalid_permission_raises(vault_file):
    with pytest.raises(AccessError, match="Invalid permission"):
        revoke_access(vault_file, "ci", ["DB_HOST"], permission="delete")


# --- list_access ---

def test_list_access_all_roles(vault_file):
    grant_access(vault_file, "ci", ["DB_HOST"])
    grant_access(vault_file, "admin", ["DB_PASS"], permission="write")
    result = list_access(vault_file)
    assert "ci" in result
    assert "admin" in result


def test_list_access_specific_role(vault_file):
    grant_access(vault_file, "ci", ["API_KEY"])
    result = list_access(vault_file, role="ci")
    assert "ci" in result
    assert "API_KEY" in result["ci"]["read"]


def test_list_access_unknown_role_returns_empty_entry(vault_file):
    result = list_access(vault_file, role="nobody")
    assert result["nobody"] == {"read": [], "write": []}


# --- can_access ---

def test_can_access_true_after_grant(vault_file):
    grant_access(vault_file, "ci", ["DB_HOST"])
    assert can_access(vault_file, "ci", "DB_HOST") is True


def test_can_access_false_without_grant(vault_file):
    assert can_access(vault_file, "ci", "DB_HOST") is False


def test_can_access_read_does_not_imply_write(vault_file):
    grant_access(vault_file, "ci", ["DB_HOST"], permission="read")
    assert can_access(vault_file, "ci", "DB_HOST", "write") is False
