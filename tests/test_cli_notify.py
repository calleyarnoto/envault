"""Tests for envault.cli_notify."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_notify import cmd_notify


@pytest.fixture()
def vault_file(tmp_path: Path) -> str:
    p = tmp_path / "project.vault"
    p.write_text("{}")
    return str(p)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _invoke(runner, vault_file, *args):
    return runner.invoke(cmd_notify, [*args, vault_file])


# --- set-webhook ---

def test_set_webhook_prints_confirmation(runner, vault_file):
    result = runner.invoke(cmd_notify, ["set-webhook", vault_file, "https://hook.example.com"])
    assert result.exit_code == 0
    assert "Webhook set" in result.output
    assert "https://hook.example.com" in result.output


def test_set_webhook_invalid_url_exits_nonzero(runner, vault_file):
    result = runner.invoke(cmd_notify, ["set-webhook", vault_file, "ftp://bad"])
    assert result.exit_code != 0
    assert "Invalid webhook URL" in result.output


def test_set_webhook_missing_vault_exits_nonzero(runner, tmp_path):
    missing = str(tmp_path / "gone.vault")
    result = runner.invoke(cmd_notify, ["set-webhook", missing, "https://x.com"])
    assert result.exit_code != 0


# --- show ---

def test_show_no_webhook_configured(runner, vault_file):
    result = runner.invoke(cmd_notify, ["show", vault_file])
    assert result.exit_code == 0
    assert "No webhook configured" in result.output


def test_show_displays_webhook_url(runner, vault_file):
    runner.invoke(cmd_notify, ["set-webhook", vault_file, "https://example.com/hook"])
    result = runner.invoke(cmd_notify, ["show", vault_file])
    assert result.exit_code == 0
    assert "https://example.com/hook" in result.output


# --- clear ---

def test_clear_webhook_prints_cleared(runner, vault_file):
    runner.invoke(cmd_notify, ["set-webhook", vault_file, "https://example.com/hook"])
    result = runner.invoke(cmd_notify, ["clear", vault_file])
    assert result.exit_code == 0
    assert "cleared" in result.output.lower()


def test_clear_webhook_removes_url(runner, vault_file):
    runner.invoke(cmd_notify, ["set-webhook", vault_file, "https://example.com/hook"])
    runner.invoke(cmd_notify, ["clear", vault_file])
    result = runner.invoke(cmd_notify, ["show", vault_file])
    assert "No webhook configured" in result.output


# --- test ---

def test_notify_test_no_webhook_configured(runner, vault_file):
    result = runner.invoke(cmd_notify, ["test", vault_file])
    assert result.exit_code == 0
    assert "nothing sent" in result.output


def test_notify_test_sends_when_webhook_set(runner, vault_file):
    runner.invoke(cmd_notify, ["set-webhook", vault_file, "https://hook.example.com"])

    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = runner.invoke(cmd_notify, ["test", vault_file])

    assert result.exit_code == 0
    assert "sent" in result.output


def test_notify_test_delivery_failure_exits_nonzero(runner, vault_file):
    runner.invoke(cmd_notify, ["set-webhook", vault_file, "https://hook.example.com"])

    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        result = runner.invoke(cmd_notify, ["test", vault_file])

    assert result.exit_code != 0
