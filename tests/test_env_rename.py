"""Tests for envault.env_rename."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_rename import RenameError, rename_secret
from envault.tags import add_tag, list_tags
from envault.ttl import set_ttl, get_ttl


PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    v = Vault(p, PASS)
    v.init()
    v.set("API_KEY", "abc123")
    v.set("DB_URL", "postgres://localhost/db")
    return p


def test_rename_basic(vault_file: Path) -> None:
    rename_secret(vault_file, PASS, "API_KEY", "API_TOKEN")
    v = Vault(vault_file, PASS)
    assert v.get("API_TOKEN") == "abc123"


def test_rename_removes_old_key(vault_file: Path) -> None:
    rename_secret(vault_file, PASS, "API_KEY", "API_TOKEN")
    v = Vault(vault_file, PASS)
    assert "API_KEY" not in v.all()


def test_rename_same_key_raises(vault_file: Path) -> None:
    with pytest.raises(RenameError, match="identical"):
        rename_secret(vault_file, PASS, "API_KEY", "API_KEY")


def test_rename_missing_key_raises(vault_file: Path) -> None:
    with pytest.raises(RenameError, match="not found"):
        rename_secret(vault_file, PASS, "GHOST", "SPIRIT")


def test_rename_existing_target_raises_without_overwrite(vault_file: Path) -> None:
    with pytest.raises(RenameError, match="already exists"):
        rename_secret(vault_file, PASS, "API_KEY", "DB_URL")


def test_rename_existing_target_succeeds_with_overwrite(vault_file: Path) -> None:
    rename_secret(vault_file, PASS, "API_KEY", "DB_URL", overwrite=True)
    v = Vault(vault_file, PASS)
    assert v.get("DB_URL") == "abc123"
    assert "API_KEY" not in v.all()


def test_rename_migrates_tags(vault_file: Path) -> None:
    add_tag(vault_file, "API_KEY", "infra")
    rename_secret(vault_file, PASS, "API_KEY", "API_TOKEN")
    assert "infra" in list_tags(vault_file, "API_TOKEN")
    assert list_tags(vault_file, "API_KEY") == set()


def test_rename_migrates_ttl(vault_file: Path) -> None:
    set_ttl(vault_file, "API_KEY", 3600)
    rename_secret(vault_file, PASS, "API_KEY", "API_TOKEN")
    assert get_ttl(vault_file, "API_TOKEN") is not None
    assert get_ttl(vault_file, "API_KEY") is None


def test_rename_missing_vault_raises(tmp_path: Path) -> None:
    ghost = tmp_path / "ghost.vault"
    with pytest.raises(Exception):
        rename_secret(ghost, PASS, "X", "Y")
