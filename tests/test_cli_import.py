"""Tests for the `envault import` CLI command."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli import cli
from envault.vault import Vault


@pytest.fixture()
def vault_file(tmp_path):
    path = tmp_path / ".envault"
    Vault.init(path, "secret")
    return path


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("ALPHA=one\nBETA=two\n", encoding="utf-8")
    return p


def _invoke(vault_file, env_file, extra_args=None):
    runner = CliRunner()
    args = [
        "import",
        str(env_file),
        "--vault", str(vault_file),
        "--passphrase", "secret",
    ]
    if extra_args:
        args.extend(extra_args)
    return runner.invoke(cli, args, catch_exceptions=False)


def test_import_success_message(vault_file, env_file):
    result = _invoke(vault_file, env_file)
    assert result.exit_code == 0
    assert "imported" in result.output
    assert "ALPHA" in result.output
    assert "BETA" in result.output


def test_import_summary_line(vault_file, env_file):
    result = _invoke(vault_file, env_file)
    assert "2 imported" in result.output


def test_import_values_stored(vault_file, env_file):
    _invoke(vault_file, env_file)
    vault = Vault.load(vault_file, "secret")
    assert vault.get("ALPHA") == "one"
    assert vault.get("BETA") == "two"


def test_import_skip_existing(vault_file, env_file, tmp_path):
    # Pre-populate ALPHA
    v = Vault.load(vault_file, "secret")
    v.set("ALPHA", "original")
    v.save("secret")

    result = _invoke(vault_file, env_file)
    assert "skipped" in result.output
    assert Vault.load(vault_file, "secret").get("ALPHA") == "original"


def test_import_overwrite_flag(vault_file, env_file):
    v = Vault.load(vault_file, "secret")
    v.set("ALPHA", "original")
    v.save("secret")

    result = _invoke(vault_file, env_file, ["--overwrite"])
    assert "overwritten" in result.output
    assert Vault.load(vault_file, "secret").get("ALPHA") == "one"


def test_import_missing_vault(tmp_path, env_file):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "import", str(env_file),
            "--vault", str(tmp_path / "no.vault"),
            "--passphrase", "x",
        ],
    )
    assert result.exit_code != 0
    assert "Vault not found" in result.output


def test_import_empty_env_file(vault_file, tmp_path):
    empty = tmp_path / "empty.env"
    empty.write_text("", encoding="utf-8")
    result = _invoke(vault_file, empty)
    assert "Nothing to import" in result.output
