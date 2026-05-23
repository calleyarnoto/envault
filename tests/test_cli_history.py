"""Tests for envault.cli_history."""
import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.vault import Vault
from envault.cli_history import cmd_history
from envault.env_history import record

PASSPHRASE = "cli-hist-pass"


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / ".envault"
    v = Vault(p)
    v.init(PASSPHRASE)
    v.set("DB_URL", "postgres://localhost/db", PASSPHRASE)
    return p


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, vault_file, *args):
    return runner.invoke(
        cmd_history,
        [*args, "--vault", str(vault_file)],
        catch_exceptions=False,
    )


# --- history list ---

def test_list_no_history_message(runner, vault_file):
    result = _invoke(runner, vault_file, "list", "DB_URL")
    assert result.exit_code == 0
    assert "No history" in result.output


def test_list_shows_entries(runner, vault_file):
    record(vault_file, "DB_URL", "postgres://localhost/db")
    record(vault_file, "DB_URL", "postgres://prod/db")
    result = _invoke(runner, vault_file, "list", "DB_URL")
    assert result.exit_code == 0
    assert "2 entries" in result.output
    assert "postgres://localhost/db" in result.output
    assert "postgres://prod/db" in result.output


def test_list_shows_note(runner, vault_file):
    record(vault_file, "DB_URL", "v", note="initial")
    result = _invoke(runner, vault_file, "list", "DB_URL")
    assert "initial" in result.output


def test_list_missing_vault_exits_nonzero(runner, tmp_path):
    result = runner.invoke(
        cmd_history,
        ["list", "KEY", "--vault", str(tmp_path / "missing.vault")],
    )
    assert result.exit_code != 0


# --- history record ---

def test_record_prints_confirmation(runner, vault_file):
    result = _invoke(runner, vault_file, "record", "DB_URL", "newval")
    assert result.exit_code == 0
    assert "Recorded" in result.output
    assert "DB_URL" in result.output


def test_record_with_note(runner, vault_file):
    result = _invoke(runner, vault_file, "record", "DB_URL", "v", "--note", "manual")
    assert result.exit_code == 0


def test_record_missing_vault_exits_nonzero(runner, tmp_path):
    result = runner.invoke(
        cmd_history,
        ["record", "KEY", "val", "--vault", str(tmp_path / "missing.vault")],
    )
    assert result.exit_code != 0


# --- history clear ---

def test_clear_specific_key_with_yes_flag(runner, vault_file):
    record(vault_file, "DB_URL", "v")
    result = _invoke(runner, vault_file, "clear", "DB_URL", "--yes")
    assert result.exit_code == 0
    assert "Cleared 1" in result.output


def test_clear_all_keys_with_yes_flag(runner, vault_file):
    record(vault_file, "DB_URL", "v1")
    record(vault_file, "DB_URL", "v2")
    result = _invoke(runner, vault_file, "clear", "--yes")
    assert result.exit_code == 0
    assert "Cleared 2" in result.output


def test_clear_missing_vault_exits_nonzero(runner, tmp_path):
    result = runner.invoke(
        cmd_history,
        ["clear", "--yes", "--vault", str(tmp_path / "missing.vault")],
    )
    assert result.exit_code != 0
