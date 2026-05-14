"""Tests for envault.search."""

from __future__ import annotations

import pytest

from envault.search import SearchError, SearchResult, search_secrets
from envault.vault import Vault

PASSPHRASE = "hunter2"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(tmp_path / "vault.json")
    v.init(PASSPHRASE)
    v.set("AWS_ACCESS_KEY", "AKIA1234", PASSPHRASE)
    v.set("AWS_SECRET_KEY", "secret_value", PASSPHRASE)
    v.set("DATABASE_URL", "postgres://localhost/db", PASSPHRASE)
    v.set("DEBUG", "true", PASSPHRASE)
    return v


def test_no_filter_raises(vault):
    with pytest.raises(SearchError, match="at least one"):
        search_secrets(vault, PASSPHRASE)


def test_key_pattern_glob_match(vault):
    results = search_secrets(vault, PASSPHRASE, key_pattern="AWS_*")
    keys = {r.key for r in results}
    assert keys == {"AWS_ACCESS_KEY", "AWS_SECRET_KEY"}


def test_key_pattern_no_match_returns_empty(vault):
    results = search_secrets(vault, PASSPHRASE, key_pattern="NONEXISTENT_*")
    assert results == []


def test_key_pattern_case_insensitive_by_default(vault):
    results = search_secrets(vault, PASSPHRASE, key_pattern="aws_*")
    assert len(results) == 2


def test_key_pattern_case_sensitive(vault):
    results = search_secrets(
        vault, PASSPHRASE, key_pattern="aws_*", case_sensitive=True
    )
    assert results == []


def test_value_substring_match(vault):
    results = search_secrets(vault, PASSPHRASE, value_substring="postgres")
    assert len(results) == 1
    assert results[0].key == "DATABASE_URL"


def test_value_substring_case_insensitive(vault):
    results = search_secrets(vault, PASSPHRASE, value_substring="POSTGRES")
    assert len(results) == 1


def test_value_substring_case_sensitive_no_match(vault):
    results = search_secrets(
        vault, PASSPHRASE, value_substring="POSTGRES", case_sensitive=True
    )
    assert results == []


def test_combined_key_and_value_filter(vault):
    # key matches AWS_* AND value contains 'secret'
    results = search_secrets(
        vault, PASSPHRASE, key_pattern="AWS_*", value_substring="secret"
    )
    assert len(results) == 1
    assert results[0].key == "AWS_SECRET_KEY"


def test_results_are_search_result_instances(vault):
    results = search_secrets(vault, PASSPHRASE, key_pattern="DEBUG")
    assert all(isinstance(r, SearchResult) for r in results)


def test_results_sorted_by_key(vault):
    results = search_secrets(vault, PASSPHRASE, key_pattern="AWS_*")
    keys = [r.key for r in results]
    assert keys == sorted(keys)


def test_wrong_passphrase_raises_search_error(vault):
    with pytest.raises(SearchError, match="Could not decrypt"):
        search_secrets(vault, "wrong_pass", key_pattern="AWS_*")
