"""CLI tests for the share commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_share import cmd_share


PASS = "vault-pass"
SHARE_PASS = "share-pass"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / ".envault"
    v = Vault(path)
    v.init(PASS)
    v.set(PASS, "TOKEN", "abc123")
    v.set(PASS, "HOST", "example.com")
    return path


@pytest.fixture()
def runner() -> Runner:
    return CliRunner()


def _invoke(runner, vault_file, *args, input_text=""):
    return runner.invoke(
        cmd_share,
        ["--vault", str(vault_file)] + list(args),
        input=input_text,
        catch_exceptions=False,
    )


def test_create_share_to_stdout(vault_file, tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cmd_share,
        ["create", "--vault", str(vault_file), "TOKEN"],
        input=f"{PASS}\n{SHARE_PASS}\n{SHARE_PASS}\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    # Output should be the encrypted bundle (non-empty string)
    assert len(result.output.strip()) > 10


def test_create_share_to_file(vault_file, tmp_path):
    out = tmp_path / "bundle.enc"
    runner = CliRunner()
    result = runner.invoke(
        cmd_share,
        ["create", "--vault", str(vault_file), "--out", str(out), "TOKEN"],
        input=f"{PASS}\n{SHARE_PASS}\n{SHARE_PASS}\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "written to" in result.output
    assert out.exists()


def test_create_share_missing_key_shows_error(vault_file):
    runner = CliRunner()
    result = runner.invoke(
        cmd_share,
        ["create", "--vault", str(vault_file), "MISSING"],
        input=f"{PASS}\n{SHARE_PASS}\n{SHARE_PASS}\n",
    )
    assert result.exit_code != 0
    assert "Keys not found" in result.output


def test_import_share_success(vault_file, tmp_path):
    runner = CliRunner()
    out = tmp_path / "bundle.enc"
    # Create bundle
    runner.invoke(
        cmd_share,
        ["create", "--vault", str(vault_file), "--out", str(out), "TOKEN"],
        input=f"{PASS}\n{SHARE_PASS}\n{SHARE_PASS}\n",
        catch_exceptions=False,
    )

    dest = tmp_path / "dest.vault"
    dv = Vault(dest)
    dv.init(PASS)

    result = runner.invoke(
        cmd_share,
        ["import", "--vault", str(dest), str(out)],
        input=f"{PASS}\n{SHARE_PASS}\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Imported 1 secret(s)" in result.output
