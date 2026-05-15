"""Tests for envault.env_alias."""
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_alias import (
    AliasError,
    add_alias,
    remove_alias,
    resolve_alias,
    list_aliases,
    _alias_path,
)

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path):
    vp = tmp_path / "vault.env"
    v = Vault(vp, PASS)
    v.init()
    v.set("DB_URL", "postgres://localhost/mydb")
    v.set("API_KEY", "supersecret")
    return vp


def test_add_alias_returns_resolved_value(vault_file):
    val = add_alias(vault_file, "database", "DB_URL", PASS)
    assert val == "postgres://localhost/mydb"


def test_add_alias_creates_alias_file(vault_file):
    add_alias(vault_file, "database", "DB_URL", PASS)
    assert _alias_path(vault_file).exists()


def test_add_alias_persisted_in_list(vault_file):
    add_alias(vault_file, "database", "DB_URL", PASS)
    aliases = list_aliases(vault_file)
    assert any(a["alias"] == "database" and a["target"] == "DB_URL" for a in aliases)


def test_add_alias_empty_name_raises(vault_file):
    with pytest.raises(AliasError, match="empty"):
        add_alias(vault_file, "  ", "DB_URL", PASS)


def test_add_alias_same_name_as_key_raises(vault_file):
    with pytest.raises(AliasError, match="differ"):
        add_alias(vault_file, "DB_URL", "DB_URL", PASS)


def test_add_alias_missing_target_raises(vault_file):
    with pytest.raises(AliasError, match="does not exist"):
        add_alias(vault_file, "ghost", "NONEXISTENT", PASS)


def test_resolve_alias_returns_value(vault_file):
    add_alias(vault_file, "key", "API_KEY", PASS)
    assert resolve_alias(vault_file, "key", PASS) == "supersecret"


def test_resolve_unknown_alias_raises(vault_file):
    with pytest.raises(AliasError, match="not found"):
        resolve_alias(vault_file, "nope", PASS)


def test_remove_alias(vault_file):
    add_alias(vault_file, "database", "DB_URL", PASS)
    remove_alias(vault_file, "database")
    assert not any(a["alias"] == "database" for a in list_aliases(vault_file))


def test_remove_nonexistent_alias_raises(vault_file):
    with pytest.raises(AliasError, match="not found"):
        remove_alias(vault_file, "ghost")


def test_list_aliases_sorted(vault_file):
    add_alias(vault_file, "z_alias", "DB_URL", PASS)
    add_alias(vault_file, "a_alias", "API_KEY", PASS)
    names = [a["alias"] for a in list_aliases(vault_file)]
    assert names == sorted(names)


def test_list_aliases_empty_when_no_file(vault_file):
    assert list_aliases(vault_file) == []
