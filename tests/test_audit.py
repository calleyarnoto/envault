"""Tests for envault.audit module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import (
    AUDIT_LOG_FILENAME,
    AuditEntry,
    append_audit_entry,
    load_audit_log,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    """Return a fake vault file path inside a temp directory."""
    return tmp_path / "project.vault"


def test_load_audit_log_empty_when_no_file(vault_path: Path):
    entries = load_audit_log(vault_path)
    assert entries == []


def test_append_creates_log_file(vault_path: Path):
    append_audit_entry(vault_path, action="init")
    log_path = vault_path.parent / AUDIT_LOG_FILENAME
    assert log_path.exists()


def test_append_returns_audit_entry(vault_path: Path):
    entry = append_audit_entry(vault_path, action="set", key="API_KEY")
    assert isinstance(entry, AuditEntry)
    assert entry.action == "set"
    assert entry.key == "API_KEY"


def test_append_persists_multiple_entries(vault_path: Path):
    append_audit_entry(vault_path, action="init")
    append_audit_entry(vault_path, action="set", key="DB_URL")
    append_audit_entry(vault_path, action="get", key="DB_URL")

    entries = load_audit_log(vault_path)
    assert len(entries) == 3
    assert entries[0].action == "init"
    assert entries[1].key == "DB_URL"
    assert entries[2].action == "get"


def test_entry_has_timestamp(vault_path: Path):
    entry = append_audit_entry(vault_path, action="delete", key="SECRET")
    assert entry.timestamp  # non-empty string
    assert "T" in entry.timestamp  # ISO format check


def test_entry_has_user(vault_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("USER", "alice")
    entry = append_audit_entry(vault_path, action="init")
    assert entry.user == "alice"


def test_explicit_user_overrides_env(vault_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("USER", "alice")
    entry = append_audit_entry(vault_path, action="init", user="ci-bot")
    assert entry.user == "ci-bot"


def test_log_file_is_valid_json(vault_path: Path):
    append_audit_entry(vault_path, action="set", key="TOKEN")
    log_path = vault_path.parent / AUDIT_LOG_FILENAME
    with log_path.open() as fh:
        data = json.load(fh)
    assert isinstance(data, list)
    assert data[0]["action"] == "set"


def test_audit_entry_from_dict_roundtrip():
    original = AuditEntry(action="get", key="FOO", user="bob", timestamp="2024-01-01T00:00:00+00:00")
    restored = AuditEntry.from_dict(original.to_dict())
    assert restored.action == original.action
    assert restored.key == original.key
    assert restored.user == original.user
    assert restored.timestamp == original.timestamp
