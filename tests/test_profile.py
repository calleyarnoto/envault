"""Tests for envault.profile."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.profile import (
    ProfileError,
    create_profile,
    list_profiles,
    get_profile_keys,
    delete_profile,
    export_profile,
    PROFILE_FILE,
)

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vp = tmp_path / "vault.env"
    v = Vault(vp)
    v.init(PASS)
    v.load(PASS)
    for key, val in [("DB_HOST", "localhost"), ("DB_PORT", "5432"), ("API_KEY", "abc123")]:
        v.set(key, val, PASS)
    return vp


def test_create_profile_returns_key_count(vault_file):
    count = create_profile(vault_file, "dev", ["DB_HOST", "DB_PORT"], PASS)
    assert count == 2


def test_create_profile_creates_profile_file(vault_file):
    create_profile(vault_file, "dev", ["DB_HOST"], PASS)
    assert (vault_file.parent / PROFILE_FILE).exists()


def test_list_profiles_empty_when_no_file(vault_file):
    assert list_profiles(vault_file) == []


def test_list_profiles_returns_sorted_names(vault_file):
    create_profile(vault_file, "prod", ["API_KEY"], PASS)
    create_profile(vault_file, "dev", ["DB_HOST"], PASS)
    assert list_profiles(vault_file) == ["dev", "prod"]


def test_get_profile_keys_returns_correct_keys(vault_file):
    create_profile(vault_file, "dev", ["DB_HOST", "DB_PORT"], PASS)
    keys = get_profile_keys(vault_file, "dev")
    assert keys == ["DB_HOST", "DB_PORT"]


def test_get_profile_keys_missing_profile_raises(vault_file):
    with pytest.raises(ProfileError, match="does not exist"):
        get_profile_keys(vault_file, "ghost")


def test_create_profile_missing_key_raises(vault_file):
    with pytest.raises(ProfileError, match="Keys not found"):
        create_profile(vault_file, "dev", ["NONEXISTENT"], PASS)


def test_create_profile_empty_name_raises(vault_file):
    with pytest.raises(ProfileError, match="must not be empty"):
        create_profile(vault_file, "  ", ["DB_HOST"], PASS)


def test_create_profile_no_keys_raises(vault_file):
    with pytest.raises(ProfileError, match="At least one key"):
        create_profile(vault_file, "dev", [], PASS)


def test_delete_profile_removes_it(vault_file):
    create_profile(vault_file, "dev", ["DB_HOST"], PASS)
    delete_profile(vault_file, "dev")
    assert "dev" not in list_profiles(vault_file)


def test_delete_nonexistent_profile_raises(vault_file):
    with pytest.raises(ProfileError, match="does not exist"):
        delete_profile(vault_file, "ghost")


def test_export_profile_returns_secret_values(vault_file):
    create_profile(vault_file, "db", ["DB_HOST", "DB_PORT"], PASS)
    result = export_profile(vault_file, "db", PASS)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_create_profile_deduplicates_keys(vault_file):
    count = create_profile(vault_file, "dev", ["DB_HOST", "DB_HOST", "DB_PORT"], PASS)
    assert count == 2
