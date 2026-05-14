"""Tests for the 'rotate' CLI sub-command."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_rotate import cmd_rotate
from envault.vault import Vault


OLD_PASS = "hunter2"
NEW_PASS = "c0rrect-h0rse"


@pytest.fixture()
def vault_file(tmp_path):
    path = tmp_path / "vault.json"
    v = Vault(path, OLD_PASS)
    v.init()
    v.set("DB_URL", "postgres://localhost/mydb")
    return path


def _invoke(vault_file, old_pass=OLD_PASS, new_pass=NEW_PASS, extra_args=None):
    runner = CliRunner()
    args = [
        "--vault", str(vault_file),
        "--old-passphrase", old_pass,
        "--new-passphrase", new_pass,
        "--new-passphrase-confirmation", new_pass,
    ]
    if extra_args:
        args += extra_args
    return runner.invoke(cmd_rotate, args, catch_exceptions=False)


def test_rotate_success_message(vault_file):
    result = _invoke(vault_file)
    assert result.exit_code == 0
    assert "1 secret(s) re-encrypted" in result.output


def test_rotate_wrong_old_passphrase(vault_file):
    result = _invoke(vault_file, old_pass="wrong")
    assert result.exit_code != 0
    assert "Error" in result.output


def test_rotate_same_passphrase(vault_file):
    result = _invoke(vault_file, new_pass=OLD_PASS)
    assert result.exit_code != 0
    assert "Error" in result.output


def test_rotate_missing_vault(tmp_path):
    missing = tmp_path / "ghost.json"
    result = _invoke(missing)
    assert result.exit_code != 0
    assert "Error" in result.output


def test_rotate_with_audit_log(vault_file, tmp_path):
    log_path = tmp_path / "audit.log"
    result = _invoke(vault_file, extra_args=["--audit-log", str(log_path)])
    assert result.exit_code == 0
    assert log_path.exists()
