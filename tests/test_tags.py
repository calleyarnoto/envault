"""Tests for envault.tags — tag-based secret grouping."""

import pytest

from envault.vault import Vault
from envault.tags import (
    TagError,
    add_tag,
    remove_tag,
    list_tags,
    keys_for_tag,
    all_tags,
)

PASS = "hunter2"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(tmp_path / "vault.json")
    v.init(PASS)
    v.set("DB_URL", "postgres://localhost/db", PASS)
    v.set("API_KEY", "secret-key", PASS)
    v.set("CACHE_URL", "redis://localhost", PASS)
    return v


def test_add_tag_and_list(vault):
    add_tag(vault, "DB_URL", "database", PASS)
    assert "database" in list_tags(vault, "DB_URL")


def test_add_tag_idempotent(vault):
    add_tag(vault, "DB_URL", "database", PASS)
    add_tag(vault, "DB_URL", "database", PASS)
    assert list_tags(vault, "DB_URL").count("database") == 1


def test_add_empty_tag_raises(vault):
    with pytest.raises(TagError):
        add_tag(vault, "DB_URL", "", PASS)


def test_multiple_tags_on_same_key(vault):
    add_tag(vault, "DB_URL", "database", PASS)
    add_tag(vault, "DB_URL", "production", PASS)
    tags = list_tags(vault, "DB_URL")
    assert "database" in tags
    assert "production" in tags


def test_remove_tag_returns_true_when_present(vault):
    add_tag(vault, "API_KEY", "external", PASS)
    result = remove_tag(vault, "API_KEY", "external", PASS)
    assert result is True
    assert "external" not in list_tags(vault, "API_KEY")


def test_remove_tag_returns_false_when_absent(vault):
    result = remove_tag(vault, "API_KEY", "nonexistent", PASS)
    assert result is False


def test_keys_for_tag_single(vault):
    add_tag(vault, "DB_URL", "database", PASS)
    add_tag(vault, "CACHE_URL", "database", PASS)
    keys = keys_for_tag(vault, "database")
    assert "DB_URL" in keys
    assert "CACHE_URL" in keys
    assert "API_KEY" not in keys


def test_keys_for_tag_no_matches(vault):
    assert keys_for_tag(vault, "nonexistent") == []


def test_list_tags_unknown_key_returns_empty(vault):
    assert list_tags(vault, "UNKNOWN_KEY") == []


def test_all_tags_excludes_internal_key(vault):
    add_tag(vault, "API_KEY", "external", PASS)
    mapping = all_tags(vault)
    assert "__tags__" not in mapping
    assert "API_KEY" in mapping
