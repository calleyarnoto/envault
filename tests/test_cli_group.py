"""CLI tests for envault group commands."""
from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.vault import Vault
from envault.cli_group import cmd_group

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "vault.env"
    v = Vault(p)
    v.init(PASS)
    v.set("DB_HOST", "localhost", PASS)
    v.set("DB_PORT", "5432", PASS)
    v.set("API_KEY", "abc", PASS)
    return p


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _invoke(runner, vault_file, *args, passphrase=PASS):
    extra = ["--passphrase", passphrase] if passphrase else []
    return runner.invoke(
        cmd_group,
        ["--vault", str(vault_file), *args, *extra],
        catch_exceptions=False,
    )


def test_create_success_message(runner, vault_file):
    result = _invoke(runner, vault_file, "create", "db", "DB_HOST", "DB_PORT")
    assert result.exit_code == 0
    assert "Group 'db' saved with 2 key(s)" in result.output


def test_create_missing_key_exits_nonzero(runner, vault_file):
    result = runner.invoke(
        cmd_group,
        ["create", "bad", "MISSING", "--vault", str(vault_file), "--passphrase", PASS],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert "MISSING" in result.output


def test_list_no_groups(runner, vault_file):
    result = runner.invoke(
        cmd_group,
        ["list", "--vault", str(vault_file)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "No groups defined" in result.output


def test_list_shows_created_group(runner, vault_file):
    _invoke(runner, vault_file, "create", "db", "DB_HOST")
    result = runner.invoke(
        cmd_group,
        ["list", "--vault", str(vault_file)],
        catch_exceptions=False,
    )
    assert "db" in result.output
    assert "DB_HOST" in result.output


def test_delete_removes_group(runner, vault_file):
    _invoke(runner, vault_file, "create", "db", "DB_HOST")
    result = runner.invoke(
        cmd_group,
        ["delete", "db", "--vault", str(vault_file)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_show_prints_key_values(runner, vault_file):
    _invoke(runner, vault_file, "create", "db", "DB_HOST", "DB_PORT")
    result = _invoke(runner, vault_file, "show", "db")
    assert "DB_HOST=localhost" in result.output
    assert "DB_PORT=5432" in result.output
