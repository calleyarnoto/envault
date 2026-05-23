"""Tests for envault.env_group."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_group import (
    GroupError,
    create_group,
    delete_group,
    list_groups,
    get_group_secrets,
    _group_path,
)

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "vault.env"
    v = Vault(p)
    v.init(PASS)
    v.set("DB_HOST", "localhost", PASS)
    v.set("DB_PORT", "5432", PASS)
    v.set("API_KEY", "secret123", PASS)
    return p


def test_create_group_returns_key_count(vault_file):
    count = create_group(vault_file, "database", ["DB_HOST", "DB_PORT"], PASS)
    assert count == 2


def test_create_group_persists_file(vault_file):
    create_group(vault_file, "database", ["DB_HOST"], PASS)
    groups = _group_path(vault_file)
    assert groups.exists()
    data = json.loads(groups.read_text())
    assert "database" in data
    assert "DB_HOST" in data["database"]


def test_create_group_idempotent(vault_file):
    create_group(vault_file, "database", ["DB_HOST"], PASS)
    count = create_group(vault_file, "database", ["DB_HOST", "DB_PORT"], PASS)
    assert count == 2


def test_create_group_empty_name_raises(vault_file):
    with pytest.raises(GroupError, match="empty"):
        create_group(vault_file, "  ", ["DB_HOST"], PASS)


def test_create_group_missing_key_raises(vault_file):
    with pytest.raises(GroupError, match="MISSING_KEY"):
        create_group(vault_file, "bad", ["MISSING_KEY"], PASS)


def test_create_group_missing_vault_raises(tmp_path):
    with pytest.raises(GroupError, match="Vault not found"):
        create_group(tmp_path / "no.env", "g", [], PASS)


def test_list_groups_empty_when_no_file(vault_file):
    assert list_groups(vault_file) == {}


def test_list_groups_returns_all(vault_file):
    create_group(vault_file, "db", ["DB_HOST", "DB_PORT"], PASS)
    create_group(vault_file, "api", ["API_KEY"], PASS)
    groups = list_groups(vault_file)
    assert set(groups.keys()) == {"db", "api"}


def test_delete_group_removes_entry(vault_file):
    create_group(vault_file, "db", ["DB_HOST"], PASS)
    delete_group(vault_file, "db")
    assert "db" not in list_groups(vault_file)


def test_delete_nonexistent_group_raises(vault_file):
    with pytest.raises(GroupError, match="does not exist"):
        delete_group(vault_file, "ghost")


def test_get_group_secrets_returns_values(vault_file):
    create_group(vault_file, "db", ["DB_HOST", "DB_PORT"], PASS)
    result = get_group_secrets(vault_file, "db", PASS)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_get_group_secrets_unknown_group_raises(vault_file):
    with pytest.raises(GroupError, match="does not exist"):
        get_group_secrets(vault_file, "nope", PASS)
