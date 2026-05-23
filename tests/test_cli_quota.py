"""Tests for envault.cli_quota."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_quota import cmd_quota
from envault.env_quota import set_quota

PASS = "cli-quota-pass"


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "v.vault"
    Vault(p, PASS).init()
    return p


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, vault_file, *args):
    return runner.invoke(cmd_quota, [*args, str(vault_file)])


# --- quota set ---

def test_set_prints_confirmation(runner, vault_file):
    result = runner.invoke(cmd_quota, ["set", str(vault_file), "20"])
    assert result.exit_code == 0
    assert "20" in result.output
    assert "Quota set" in result.output


def test_set_zero_exits_nonzero(runner, vault_file):
    result = runner.invoke(cmd_quota, ["set", str(vault_file), "0"])
    assert result.exit_code != 0


def test_set_missing_vault_exits_nonzero(runner, tmp_path):
    missing = tmp_path / "nope.vault"
    result = runner.invoke(cmd_quota, ["set", str(missing), "5"])
    assert result.exit_code != 0


# --- quota show ---

def test_show_no_quota_configured(runner, vault_file):
    result = runner.invoke(cmd_quota, ["show", str(vault_file)])
    assert result.exit_code == 0
    assert "No quota" in result.output


def test_show_limit_without_passphrase(runner, vault_file):
    set_quota(vault_file, 15)
    result = runner.invoke(cmd_quota, ["show", str(vault_file)])
    assert result.exit_code == 0
    assert "15" in result.output


def test_show_with_passphrase_displays_usage(runner, vault_file):
    set_quota(vault_file, 10)
    result = runner.invoke(
        cmd_quota, ["show", "--passphrase", PASS, str(vault_file)]
    )
    assert result.exit_code == 0
    assert "/10" in result.output
    assert "OK" in result.output


def test_show_at_limit_displays_at_limit(runner, vault_file):
    v = Vault(vault_file, PASS)
    v.set("KEY", "val")
    set_quota(vault_file, 1)
    result = runner.invoke(
        cmd_quota, ["show", "--passphrase", PASS, str(vault_file)]
    )
    assert result.exit_code == 0
    assert "AT LIMIT" in result.output


# --- quota clear ---

def test_clear_prints_confirmation(runner, vault_file):
    set_quota(vault_file, 5)
    result = runner.invoke(cmd_quota, ["clear", str(vault_file)])
    assert result.exit_code == 0
    assert "cleared" in result.output.lower()


def test_clear_idempotent(runner, vault_file):
    result = runner.invoke(cmd_quota, ["clear", str(vault_file)])
    assert result.exit_code == 0
