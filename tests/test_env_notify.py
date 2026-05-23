"""Tests for envault.env_notify."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.env_notify import (
    NotifyError,
    NotifyEvent,
    clear_webhook,
    fire,
    get_webhook,
    set_webhook,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> str:
    p = tmp_path / "test.vault"
    p.write_text("{}")
    return str(p)


# --- NotifyEvent ---

def test_notify_event_to_dict(vault_file):
    ev = NotifyEvent(vault_path=vault_file, action="set", keys=["FOO"])
    d = ev.to_dict()
    assert d["action"] == "set"
    assert d["keys"] == ["FOO"]
    assert d["vault"] == vault_file
    assert isinstance(d["timestamp"], float)


def test_notify_event_repr(vault_file):
    ev = NotifyEvent(vault_path=vault_file, action="rotate", keys=[])
    assert "rotate" in repr(ev)


# --- set_webhook / get_webhook ---

def test_set_webhook_persists(vault_file):
    set_webhook(vault_file, "https://example.com/hook")
    assert get_webhook(vault_file) == "https://example.com/hook"


def test_set_webhook_missing_vault_raises(tmp_path):
    with pytest.raises(NotifyError, match="Vault not found"):
        set_webhook(str(tmp_path / "missing.vault"), "https://x.com")


def test_set_webhook_invalid_url_raises(vault_file):
    with pytest.raises(NotifyError, match="Invalid webhook URL"):
        set_webhook(vault_file, "ftp://bad.url")


def test_get_webhook_returns_none_when_unset(vault_file):
    assert get_webhook(vault_file) is None


# --- clear_webhook ---

def test_clear_webhook_removes_url(vault_file):
    set_webhook(vault_file, "https://example.com/hook")
    clear_webhook(vault_file)
    assert get_webhook(vault_file) is None


def test_clear_webhook_no_op_when_unset(vault_file):
    # Should not raise even if no webhook is configured.
    clear_webhook(vault_file)
    assert get_webhook(vault_file) is None


# --- fire ---

def test_fire_returns_false_when_no_webhook(vault_file):
    ev = NotifyEvent(vault_path=vault_file, action="set", keys=["A"])
    assert fire(ev) is False


def test_fire_calls_webhook_and_returns_true(vault_file):
    set_webhook(vault_file, "https://example.com/hook")
    ev = NotifyEvent(vault_path=vault_file, action="set", keys=["A"])

    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = fire(ev)

    assert result is True


def test_fire_raises_on_http_error(vault_file):
    set_webhook(vault_file, "https://example.com/hook")
    ev = NotifyEvent(vault_path=vault_file, action="set", keys=["A"])

    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 500

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(NotifyError, match="HTTP 500"):
            fire(ev)


def test_fire_raises_on_connection_error(vault_file):
    set_webhook(vault_file, "https://example.com/hook")
    ev = NotifyEvent(vault_path=vault_file, action="set", keys=["A"])

    with patch("urllib.request.urlopen", side_effect=OSError("refused")):
        with pytest.raises(NotifyError, match="Webhook delivery failed"):
            fire(ev)
