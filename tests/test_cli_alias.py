"""Tests for envault.cli_alias CLI commands."""
import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_alias import cmd_alias

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path):
    vp = tmp_path / "vault.env"
    v = Vault(vp, PASS)
    v.init()
    v.set("DB_URL", "postgres://localhost/mydb")
    v.set("API_KEY", "topsecret")
    return vp


@pytest.fixture()
def runner():
    return CliRunner(mix_stderr=False)


def _invoke(runner, vault_file, *args):
    return runner.invoke(
        cmd_alias,
        ["--vault", str(vault_file)] + list(args),
        catch_exceptions=False,
    )


def test_add_alias_success_message(runner, vault_file):
    result = runner.invoke(
        cmd_alias,
        ["add", "database", "DB_URL", "--vault", str(vault_file), "--passphrase", PASS],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "database" in result.output
    assert "DB_URL" in result.output


def test_add_alias_missing_target_exits_nonzero(runner, vault_file):
    result = runner.invoke(
        cmd_alias,
        ["add", "ghost", "MISSING_KEY", "--vault", str(vault_file), "--passphrase", PASS],
    )
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_remove_alias_success(runner, vault_file):
    runner.invoke(
        cmd_alias,
        ["add", "mykey", "API_KEY", "--vault", str(vault_file), "--passphrase", PASS],
        catch_exceptions=False,
    )
    result = runner.invoke(
        cmd_alias,
        ["remove", "mykey", "--vault", str(vault_file)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_nonexistent_alias_exits_nonzero(runner, vault_file):
    result = runner.invoke(
        cmd_alias,
        ["remove", "ghost", "--vault", str(vault_file)],
    )
    assert result.exit_code != 0


def test_resolve_alias_prints_value(runner, vault_file):
    runner.invoke(
        cmd_alias,
        ["add", "myapi", "API_KEY", "--vault", str(vault_file), "--passphrase", PASS],
        catch_exceptions=False,
    )
    result = runner.invoke(
        cmd_alias,
        ["resolve", "myapi", "--vault", str(vault_file), "--passphrase", PASS],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "topsecret" in result.output


def test_list_aliases_empty_message(runner, vault_file):
    result = runner.invoke(
        cmd_alias,
        ["list", "--vault", str(vault_file)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "No aliases" in result.output


def test_list_aliases_shows_entries(runner, vault_file):
    runner.invoke(
        cmd_alias,
        ["add", "db", "DB_URL", "--vault", str(vault_file), "--passphrase", PASS],
        catch_exceptions=False,
    )
    result = runner.invoke(
        cmd_alias,
        ["list", "--vault", str(vault_file)],
        catch_exceptions=False,
    )
    assert "db" in result.output
    assert "DB_URL" in result.output
