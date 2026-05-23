"""Tests for envault.env_history."""
import time
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_history import (
    HistoryEntry,
    HistoryError,
    record,
    get_history,
    clear_history,
    _history_path,
    MAX_ENTRIES_PER_KEY,
)

PASSPHRASE = "hist-test-pass"


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "secrets.vault"
    v = Vault(p)
    v.init(PASSPHRASE)
    v.set("KEY1", "value1", PASSPHRASE)
    v.set("KEY2", "value2", PASSPHRASE)
    return p


# --- HistoryEntry ---

def test_history_entry_to_dict_roundtrip():
    e = HistoryEntry(key="A", value="v", timestamp=1000.0, note="n")
    assert HistoryEntry.from_dict(e.to_dict()) == e


def test_history_entry_repr():
    e = HistoryEntry(key="X", value="y", timestamp=42.0)
    assert "X" in repr(e)
    assert "42" in repr(e)


# --- record ---

def test_record_returns_entry(vault_file):
    e = record(vault_file, "KEY1", "v1")
    assert isinstance(e, HistoryEntry)
    assert e.key == "KEY1"
    assert e.value == "v1"


def test_record_timestamp_is_recent(vault_file):
    before = time.time()
    e = record(vault_file, "KEY1", "v")
    assert e.timestamp >= before


def test_record_with_note(vault_file):
    e = record(vault_file, "KEY1", "v", note="initial set")
    assert e.note == "initial set"


def test_record_missing_vault_raises(tmp_path):
    with pytest.raises(HistoryError):
        record(tmp_path / "missing.vault", "K", "v")


def test_record_creates_history_file(vault_file):
    record(vault_file, "KEY1", "v")
    assert _history_path(vault_file).exists()


# --- get_history ---

def test_get_history_empty_for_unrecorded_key(vault_file):
    assert get_history(vault_file, "KEY1") == []


def test_get_history_returns_entries_in_order(vault_file):
    record(vault_file, "KEY1", "first")
    record(vault_file, "KEY1", "second")
    history = get_history(vault_file, "KEY1")
    assert len(history) == 2
    assert history[0].value == "first"
    assert history[1].value == "second"


def test_get_history_independent_per_key(vault_file):
    record(vault_file, "KEY1", "a")
    record(vault_file, "KEY2", "b")
    assert len(get_history(vault_file, "KEY1")) == 1
    assert len(get_history(vault_file, "KEY2")) == 1


def test_get_history_missing_vault_raises(tmp_path):
    with pytest.raises(HistoryError):
        get_history(tmp_path / "missing.vault", "K")


# --- cap at MAX_ENTRIES_PER_KEY ---

def test_history_capped_at_max(vault_file):
    for i in range(MAX_ENTRIES_PER_KEY + 5):
        record(vault_file, "KEY1", str(i))
    history = get_history(vault_file, "KEY1")
    assert len(history) == MAX_ENTRIES_PER_KEY
    # oldest entries are dropped; last entry is most recent
    assert history[-1].value == str(MAX_ENTRIES_PER_KEY + 4)


# --- clear_history ---

def test_clear_history_specific_key(vault_file):
    record(vault_file, "KEY1", "v")
    record(vault_file, "KEY2", "v")
    removed = clear_history(vault_file, "KEY1")
    assert removed == 1
    assert get_history(vault_file, "KEY1") == []
    assert len(get_history(vault_file, "KEY2")) == 1


def test_clear_history_all_keys(vault_file):
    record(vault_file, "KEY1", "v")
    record(vault_file, "KEY2", "v")
    removed = clear_history(vault_file)
    assert removed == 2
    assert get_history(vault_file, "KEY1") == []


def test_clear_history_missing_vault_raises(tmp_path):
    with pytest.raises(HistoryError):
        clear_history(tmp_path / "missing.vault")


def test_clear_history_returns_zero_when_key_has_no_history(vault_file):
    assert clear_history(vault_file, "KEY1") == 0
