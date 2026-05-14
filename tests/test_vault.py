"""Tests for envault.vault — Vault read/write and secret management."""

import pytest
from pathlib import Path

from envault.vault import Vault, VaultError, init_vault

PASSPHRASE = "hunter2-super-secret"


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / ".envault"


@pytest.fixture()
def saved_vault(vault_path: Path) -> Vault:
    """A vault with a couple of secrets, already saved to disk."""
    v = init_vault(vault_path, PASSPHRASE)
    v.set("DB_URL", "postgres://localhost/mydb")
    v.set("API_KEY", "abc123")
    v.save()
    return v


# ---------------------------------------------------------------------------
# init_vault
# ---------------------------------------------------------------------------

def test_init_vault_creates_file(vault_path):
    init_vault(vault_path, PASSPHRASE)
    assert vault_path.exists()


def test_init_vault_raises_if_exists(vault_path):
    init_vault(vault_path, PASSPHRASE)
    with pytest.raises(VaultError, match="already exists"):
        init_vault(vault_path, PASSPHRASE)


# ---------------------------------------------------------------------------
# load / save round-trip
# ---------------------------------------------------------------------------

def test_load_restores_secrets(vault_path, saved_vault):
    v2 = Vault(vault_path, PASSPHRASE)
    v2.load()
    assert v2.get("DB_URL") == "postgres://localhost/mydb"
    assert v2.get("API_KEY") == "abc123"


def test_load_wrong_passphrase_raises(vault_path, saved_vault):
    v2 = Vault(vault_path, "wrong-passphrase")
    with pytest.raises(VaultError):
        v2.load()


def test_load_missing_file_raises(vault_path):
    v = Vault(vault_path, PASSPHRASE)
    with pytest.raises(VaultError, match="not found"):
        v.load()


# ---------------------------------------------------------------------------
# Secret CRUD
# ---------------------------------------------------------------------------

def test_set_and_get(vault_path):
    v = init_vault(vault_path, PASSPHRASE)
    v.set("FOO", "bar")
    assert v.get("FOO") == "bar"


def test_get_missing_key_returns_none(vault_path):
    v = init_vault(vault_path, PASSPHRASE)
    assert v.get("MISSING") is None


def test_delete_existing_key(vault_path, saved_vault):
    assert saved_vault.delete("API_KEY") is True
    assert saved_vault.get("API_KEY") is None


def test_delete_missing_key_returns_false(vault_path, saved_vault):
    assert saved_vault.delete("NONEXISTENT") is False


def test_list_keys_sorted(vault_path, saved_vault):
    assert saved_vault.list_keys() == ["API_KEY", "DB_URL"]


def test_export_env_format(vault_path, saved_vault):
    output = saved_vault.export_env()
    assert 'export API_KEY="abc123"' in output
    assert 'export DB_URL="postgres://localhost/mydb"' in output


def test_len(vault_path, saved_vault):
    assert len(saved_vault) == 2
