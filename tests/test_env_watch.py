"""Tests for envault.env_watch."""
from __future__ import annotations

import time
from pathlib import Path
from threading import Thread
from unittest.mock import MagicMock, patch

import pytest

from envault.vault import Vault
from envault.env_watch import (
    WatchError,
    WatchEvent,
    _diff,
    _snapshot,
    watch_vault,
)

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "vault.env"
    v = Vault(p)
    v.init(PASS)
    v.set("KEY1", "val1", PASS)
    v.set("KEY2", "val2", PASS)
    return p


# ---------------------------------------------------------------------------
# WatchEvent helpers
# ---------------------------------------------------------------------------

def test_has_changes_false_when_empty():
    assert not WatchEvent().has_changes


def test_has_changes_true_when_added():
    assert WatchEvent(added=["X"]).has_changes


def test_has_changes_true_when_removed():
    assert WatchEvent(removed=["X"]).has_changes


def test_has_changes_true_when_changed():
    assert WatchEvent(changed=["X"]).has_changes


# ---------------------------------------------------------------------------
# _diff
# ---------------------------------------------------------------------------

def test_diff_detects_added():
    event = _diff({"A": "1"}, {"A": "1", "B": "2"})
    assert event.added == ["B"]
    assert not event.removed
    assert not event.changed


def test_diff_detects_removed():
    event = _diff({"A": "1", "B": "2"}, {"A": "1"})
    assert event.removed == ["B"]


def test_diff_detects_changed():
    event = _diff({"A": "old"}, {"A": "new"})
    assert event.changed == ["A"]


def test_diff_no_change_empty_event():
    event = _diff({"A": "1"}, {"A": "1"})
    assert not event.has_changes


# ---------------------------------------------------------------------------
# _snapshot
# ---------------------------------------------------------------------------

def test_snapshot_returns_all_secrets(vault_file: Path):
    v = Vault(vault_file)
    snap = _snapshot(v, PASS)
    assert snap == {"KEY1": "val1", "KEY2": "val2"}


# ---------------------------------------------------------------------------
# watch_vault
# ---------------------------------------------------------------------------

def test_watch_raises_if_vault_missing(tmp_path: Path):
    with pytest.raises(WatchError, match="not found"):
        watch_vault(tmp_path / "missing.env", PASS, max_iterations=1)


def test_watch_raises_on_bad_passphrase(vault_file: Path):
    with pytest.raises(WatchError):
        watch_vault(vault_file, "wrong", max_iterations=1)


def test_watch_calls_on_change_callback(vault_file: Path):
    callback = MagicMock()
    v = Vault(vault_file)

    def _mutate():
        time.sleep(0.05)
        v.set("KEY3", "val3", PASS)

    t = Thread(target=_mutate, daemon=True)
    t.start()
    watch_vault(vault_file, PASS, interval=0.02, max_iterations=8, on_change=callback)
    t.join()
    assert callback.called
    event: WatchEvent = callback.call_args[0][0]
    assert "KEY3" in event.added


def test_watch_invokes_shell_cmd_on_change(vault_file: Path):
    v = Vault(vault_file)

    def _mutate():
        time.sleep(0.05)
        v.set("NEW", "secret", PASS)

    t = Thread(target=_mutate, daemon=True)
    t.start()
    with patch("envault.env_watch.subprocess.run") as mock_run:
        watch_vault(
            vault_file, PASS, interval=0.02, max_iterations=8, shell_cmd="echo hi"
        )
    t.join()
    assert mock_run.called
