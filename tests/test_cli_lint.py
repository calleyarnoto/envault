"""Tests for the `envault lint` CLI command."""
import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_lint import cmd_lint


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.env")
    Vault.init(path, "passphrase")
    v = Vault.load(path, "passphrase")
    v.set("GOOD_KEY", "supersecretvalue")
    v.save()
    return path


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, vault_file, extra_args=None):
    args = ["--vault", vault_file, "--passphrase", "passphrase"]
    if extra_args:
        args += extra_args
    return runner.invoke(cmd_lint, args, catch_exceptions=False)


def test_no_issues_message(runner, vault_file):
    result = _invoke(runner, vault_file)
    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_issue_reported_in_output(runner, vault_file):
    v = Vault.load(vault_file, "passphrase")
    v.set("bad_key", "x")
    v.save()
    result = _invoke(runner, vault_file)
    assert "key_naming" in result.output or "short_value" in result.output


def test_strict_flag_exits_nonzero_on_issues(runner, vault_file):
    v = Vault.load(vault_file, "passphrase")
    v.set("bad_key", "x")
    v.save()
    result = _invoke(runner, vault_file, extra_args=["--strict"])
    assert result.exit_code == 1


def test_no_issues_strict_exits_zero(runner, vault_file):
    result = _invoke(runner, vault_file, extra_args=["--strict"])
    assert result.exit_code == 0


def test_wrong_passphrase_exits_nonzero(runner, vault_file):
    result = runner.invoke(
        cmd_lint,
        ["--vault", vault_file, "--passphrase", "wrong"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_multiple_issues_all_reported(runner, vault_file):
    """Ensure that all lint issues are reported, not just the first one."""
    v = Vault.load(vault_file, "passphrase")
    v.set("bad_key", "x")
    v.set("another_bad_key", "y")
    v.save()
    result = _invoke(runner, vault_file)
    # Both offending keys should appear somewhere in the output
    assert "bad_key" in result.output
    assert "another_bad_key" in result.output
