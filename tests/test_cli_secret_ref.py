"""CLI tests for envault ref commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_secret_ref import cmd_ref

PASS = "cli-ref-pass"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.env")
    v = Vault(path)
    v.init(PASS)
    return path


@pytest.fixture()
def runner():
    return CliRunner(mix_stderr=False)


def _add(vault_file, key, value):
    Vault(vault_file).set(PASS, key, value)


def _invoke(runner, vault_file, *args):
    return runner.invoke(
        cmd_ref,
        [*args, "--vault", vault_file, "--passphrase", PASS],
        catch_exceptions=False,
    )


def test_resolve_plain_value(runner, vault_file):
    _add(vault_file, "MSG", "hello")
    result = _invoke(runner, vault_file, "resolve", "MSG")
    assert result.exit_code == 0
    assert "hello" in result.output


def test_resolve_with_ref(runner, vault_file):
    _add(vault_file, "HOST", "localhost")
    _add(vault_file, "URL", "http://${HOST}")
    result = _invoke(runner, vault_file, "resolve", "URL")
    assert result.exit_code == 0
    assert "http://localhost" in result.output


def test_resolve_show_refs_flag(runner, vault_file):
    _add(vault_file, "HOST", "db")
    _add(vault_file, "DSN", "postgres://${HOST}/mydb")
    result = runner.invoke(
        cmd_ref,
        ["resolve", "DSN", "--vault", vault_file, "--passphrase", PASS, "--show-refs"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "HOST" in result.output + result.stderr


def test_resolve_missing_key_exits_nonzero(runner, vault_file):
    result = _invoke(runner, vault_file, "resolve", "MISSING")
    assert result.exit_code != 0


def test_resolve_missing_ref_exits_nonzero(runner, vault_file):
    _add(vault_file, "URL", "${GHOST}")
    result = _invoke(runner, vault_file, "resolve", "URL")
    assert result.exit_code != 0


def test_resolve_all_prints_all_keys(runner, vault_file):
    _add(vault_file, "A", "alpha")
    _add(vault_file, "B", "${A}-beta")
    result = _invoke(runner, vault_file, "resolve-all")
    assert result.exit_code == 0
    assert "A=alpha" in result.output
    assert "B=alpha-beta" in result.output


def test_resolve_all_empty_vault(runner, vault_file):
    result = _invoke(runner, vault_file, "resolve-all")
    assert result.exit_code == 0
    assert "empty" in result.output.lower()
