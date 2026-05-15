"""Tests for the merge CLI sub-command."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_merge import cmd_merge


PASS_A = "srcpass"
PASS_B = "dstpass"


@pytest.fixture()
def src_file(tmp_path):
    path = str(tmp_path / "src.vault")
    v = Vault.init(path, PASS_A)
    v.set("ALPHA", "1")
    v.set("BETA", "2")
    v.save()
    return path


@pytest.fixture()
def dst_file(tmp_path):
    path = str(tmp_path / "dst.vault")
    v = Vault.init(path, PASS_B)
    v.set("BETA", "original")
    v.save()
    return path


def _invoke(src, dst, extra=None, src_pass=PASS_A, dst_pass=PASS_B):
    runner = CliRunner()
    args = ["run", src, dst, "--src-pass", src_pass, "--dst-pass", dst_pass]
    if extra:
        args.extend(extra)
    return runner.invoke(cmd_merge, args, catch_exceptions=False)


def test_merge_success_message(src_file, dst_file):
    result = _invoke(src_file, dst_file)
    assert result.exit_code == 0
    assert "Merge complete" in result.output


def test_merge_added_keys_shown(src_file, dst_file):
    result = _invoke(src_file, dst_file)
    assert "+ ALPHA" in result.output


def test_merge_skipped_key_shown(src_file, dst_file):
    result = _invoke(src_file, dst_file)
    assert "skipped" in result.output
    assert "BETA" in result.output


def test_merge_overwrite_flag(src_file, dst_file):
    result = _invoke(src_file, dst_file, extra=["--overwrite"])
    assert "overwritten" in result.output
    assert "BETA" in result.output


def test_merge_specific_key(src_file, dst_file):
    result = _invoke(src_file, dst_file, extra=["--key", "ALPHA"])
    assert "+ ALPHA" in result.output
    # BETA should not appear at all since it wasn't requested
    assert "BETA" not in result.output


def test_merge_wrong_passphrase_shows_error(src_file, dst_file):
    runner = CliRunner()
    result = runner.invoke(
        cmd_merge,
        ["run", src_file, dst_file, "--src-pass", "bad", "--dst-pass", PASS_B],
    )
    assert result.exit_code != 0
    assert "Error" in result.output
