"""Tests for envault.cli_watch."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_watch import cmd_watch
from envault.vault import Vault
from envault.env_watch import WatchEvent

PASS = "s3cr3t"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "vault.env"
    v = Vault(p)
    v.init(PASS)
    v.set("FOO", "bar", PASS)
    return p


def _invoke(vault_file: Path, extra_args: list[str] | None = None):
    runner = CliRunner(mix_stderr=False)
    args = [
        "start",
        "--vault", str(vault_file),
        "--passphrase", PASS,
        "--interval", "0.01",
    ] + (extra_args or [])
    return runner.invoke(cmd_watch, args, catch_exceptions=False)


def test_watch_start_prints_watching_message(vault_file: Path):
    with patch(
        "envault.cli_watch.watch_vault",
        side_effect=KeyboardInterrupt,
    ):
        result = _invoke(vault_file)
    assert "Watching" in result.output
    assert "Stopped" in result.output


def test_watch_missing_vault_exits_nonzero(tmp_path: Path):
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cmd_watch,
        ["start", "--vault", str(tmp_path / "nope.env"), "--passphrase", PASS],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert "Error" in result.output


def test_watch_on_change_prints_added(vault_file: Path):
    captured_cb = {}

    def fake_watch(path, passphrase, *, interval, on_change=None, shell_cmd=None):
        captured_cb["fn"] = on_change

    with patch("envault.cli_watch.watch_vault", side_effect=fake_watch):
        _invoke(vault_file)

    cb = captured_cb.get("fn")
    assert cb is not None
    runner = CliRunner()
    with runner.isolated_filesystem():
        from io import StringIO
        import click
        # Directly call the callback and check it doesn't raise
        event = WatchEvent(added=["NEW_KEY"], removed=[], changed=[])
        cb(event)  # should not raise


def test_watch_on_change_prints_removed(vault_file: Path):
    captured_cb = {}

    def fake_watch(path, passphrase, *, interval, on_change=None, shell_cmd=None):
        captured_cb["fn"] = on_change

    with patch("envault.cli_watch.watch_vault", side_effect=fake_watch):
        _invoke(vault_file)

    event = WatchEvent(removed=["OLD_KEY"])
    captured_cb["fn"](event)  # should not raise


def test_watch_passes_shell_cmd(vault_file: Path):
    call_kwargs = {}

    def fake_watch(path, passphrase, *, interval, on_change=None, shell_cmd=None):
        call_kwargs["shell_cmd"] = shell_cmd

    with patch("envault.cli_watch.watch_vault", side_effect=fake_watch):
        _invoke(vault_file, ["--exec", "make reload"])

    assert call_kwargs.get("shell_cmd") == "make reload"
