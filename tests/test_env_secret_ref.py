"""Tests for envault.env_secret_ref — secret reference resolution."""

from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.env_secret_ref import (
    RefError,
    RefResult,
    resolve_refs,
    resolve_all,
    _find_refs,
)

PASS = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.env")
    v = Vault(path)
    v.init(PASS)
    return path


def _add(vault_file, key, value):
    v = Vault(vault_file)
    v.set(PASS, key, value)


# ---------------------------------------------------------------------------
# _find_refs
# ---------------------------------------------------------------------------

def test_find_refs_empty():
    assert _find_refs("plain value") == []


def test_find_refs_single():
    assert _find_refs("hello ${NAME}") == ["NAME"]


def test_find_refs_multiple():
    refs = _find_refs("${A} and ${B}")
    assert refs == ["A", "B"]


def test_find_refs_no_partial_match():
    # $NAME without braces should not match
    assert _find_refs("$NAME") == []


# ---------------------------------------------------------------------------
# resolve_refs
# ---------------------------------------------------------------------------

def test_resolve_no_refs(vault_file):
    _add(vault_file, "GREETING", "hello world")
    result = resolve_refs(vault_file, PASS, "GREETING")
    assert result.resolved == "hello world"
    assert result.refs == []


def test_resolve_single_ref(vault_file):
    _add(vault_file, "HOST", "localhost")
    _add(vault_file, "URL", "http://${HOST}/api")
    result = resolve_refs(vault_file, PASS, "URL")
    assert result.resolved == "http://localhost/api"
    assert "HOST" in result.refs


def test_resolve_chained_refs(vault_file):
    _add(vault_file, "PROTO", "https")
    _add(vault_file, "HOST", "example.com")
    _add(vault_file, "BASE", "${PROTO}://${HOST}")
    _add(vault_file, "FULL", "${BASE}/v1")
    result = resolve_refs(vault_file, PASS, "FULL")
    assert result.resolved == "https://example.com/v1"


def test_resolve_missing_key_raises(vault_file):
    _add(vault_file, "URL", "http://${MISSING}/api")
    with pytest.raises(RefError, match="Referenced key not found"):
        resolve_refs(vault_file, PASS, "URL")


def test_resolve_unknown_top_key_raises(vault_file):
    with pytest.raises(RefError, match="Key not found"):
        resolve_refs(vault_file, PASS, "NONEXISTENT")


def test_resolve_circular_raises(vault_file):
    # A -> B -> A
    _add(vault_file, "A", "${B}")
    _add(vault_file, "B", "${A}")
    with pytest.raises(RefError, match="Circular reference"):
        resolve_refs(vault_file, PASS, "A")


def test_resolve_result_repr(vault_file):
    _add(vault_file, "X", "plain")
    result = resolve_refs(vault_file, PASS, "X")
    assert isinstance(repr(result), str)


def test_resolve_empty_passphrase_raises(vault_file):
    with pytest.raises(RefError):
        resolve_refs(vault_file, "", "KEY")


# ---------------------------------------------------------------------------
# resolve_all
# ---------------------------------------------------------------------------

def test_resolve_all_returns_dict(vault_file):
    _add(vault_file, "A", "alpha")
    _add(vault_file, "B", "${A}-beta")
    results = resolve_all(vault_file, PASS)
    assert "A" in results
    assert "B" in results
    assert results["B"].resolved == "alpha-beta"


def test_resolve_all_no_refs_unchanged(vault_file):
    _add(vault_file, "PLAIN", "value")
    results = resolve_all(vault_file, PASS)
    assert results["PLAIN"].resolved == "value"
    assert results["PLAIN"].refs == []
