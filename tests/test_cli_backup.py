"""CLI tests for the backup sub-commands."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_backup import cmd_backup


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / ".envault"
    p.write_text(json.dumps({"secrets": {"A": "1"}, "version": 1}))
    return p


def _invoke(vault_file: Path, *args: str):
    runner = CliRunner()
    return runner.invoke(cmd_backup, ["--vault", str(vault_file), *args])


# ---------------------------------------------------------------------------
# backup create
# ---------------------------------------------------------------------------

def test_create_prints_backup_path(vault_file: Path) -> None:
    result = _invoke(vault_file, "create")
    assert result.exit_code == 0
    assert "Backup created:" in result.output


def test_create_with_label(vault_file: Path) -> None:
    result = _invoke(vault_file, "create", "--label", "ci")
    assert result.exit_code == 0
    assert "ci" in result.output


def test_create_no_compress_flag(vault_file: Path) -> None:
    result = _invoke(vault_file, "create", "--no-compress")
    assert result.exit_code == 0
    # Path shown in output should not end with .gz
    line = [l for l in result.output.splitlines() if "Backup created:" in l][0]
    assert not line.strip().endswith(".gz")


def test_create_missing_vault_shows_error(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cmd_backup, ["--vault", str(tmp_path / "missing.json"), "create"])
    assert result.exit_code != 0
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# backup list
# ---------------------------------------------------------------------------

def test_list_no_backups_message(vault_file: Path) -> None:
    result = _invoke(vault_file, "list")
    assert result.exit_code == 0
    assert "No backups found" in result.output


def test_list_shows_backup_after_create(vault_file: Path) -> None:
    _invoke(vault_file, "create")
    result = _invoke(vault_file, "list")
    assert result.exit_code == 0
    assert ".bak" in result.output


# ---------------------------------------------------------------------------
# backup restore
# ---------------------------------------------------------------------------

def test_restore_success_message(vault_file: Path, tmp_path: Path) -> None:
    create_result = _invoke(vault_file, "create")
    backup_path = create_result.output.split("Backup created:")[1].strip()

    target = tmp_path / "restored.json"
    runner = CliRunner()
    result = runner.invoke(
        cmd_backup,
        ["--vault", str(target), "restore", backup_path, "--overwrite"],
    )
    assert result.exit_code == 0
    assert "restored" in result.output.lower()


def test_restore_raises_without_overwrite(vault_file: Path) -> None:
    _invoke(vault_file, "create")
    backups_result = _invoke(vault_file, "list")
    backup_path = backups_result.output.strip().splitlines()[-1]

    runner = CliRunner()
    result = runner.invoke(
        cmd_backup,
        ["--vault", str(vault_file), "restore", backup_path],
    )
    assert result.exit_code != 0
    assert "Error" in result.output
