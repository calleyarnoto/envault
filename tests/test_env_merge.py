"""Tests for envault.env_merge."""

from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.env_merge import MergeError, MergeResult, merge_vaults


PASS_A = "passA"
PASS_B = "passB"


@pytest.fixture()
def src_vault(tmp_path):
    path = str(tmp_path / "src.vault")
    v = Vault.init(path, PASS_A)
    v.set("KEY1", "alpha")
    v.set("KEY2", "beta")
    v.set("KEY3", "gamma")
    v.save()
    return path


@pytest.fixture()
def dst_vault(tmp_path):
    path = str(tmp_path / "dst.vault")
    v = Vault.init(path, PASS_B)
    v.set("KEY2", "original")
    v.save()
    return path


def test_merge_adds_new_keys(src_vault, dst_vault):
    result = merge_vaults(src_vault, PASS_A, dst_vault, PASS_B)
    assert "KEY1" in result.added
    assert "KEY3" in result.added


def test_merge_skips_existing_by_default(src_vault, dst_vault):
    result = merge_vaults(src_vault, PASS_A, dst_vault, PASS_B)
    assert "KEY2" in result.skipped
    assert "KEY2" not in result.overwritten


def test_merge_overwrites_when_flag_set(src_vault, dst_vault):
    result = merge_vaults(src_vault, PASS_A, dst_vault, PASS_B, overwrite=True)
    assert "KEY2" in result.overwritten
    assert "KEY2" not in result.skipped


def test_merge_values_persisted(src_vault, dst_vault):
    merge_vaults(src_vault, PASS_A, dst_vault, PASS_B, overwrite=True)
    dst = Vault.load(dst_vault, PASS_B)
    assert dst.get("KEY1") == "alpha"
    assert dst.get("KEY2") == "beta"


def test_merge_subset_of_keys(src_vault, dst_vault):
    result = merge_vaults(src_vault, PASS_A, dst_vault, PASS_B, keys=["KEY1"])
    assert result.added == ["KEY1"]
    assert result.skipped == []
    dst = Vault.load(dst_vault, PASS_B)
    with pytest.raises(Exception):
        dst.get("KEY3")  # KEY3 should not have been merged


def test_merge_missing_key_raises(src_vault, dst_vault):
    with pytest.raises(MergeError, match="MISSING"):
        merge_vaults(src_vault, PASS_A, dst_vault, PASS_B, keys=["MISSING"])


def test_merge_wrong_src_passphrase_raises(src_vault, dst_vault):
    with pytest.raises(MergeError, match="source"):
        merge_vaults(src_vault, "wrong", dst_vault, PASS_B)


def test_merge_wrong_dst_passphrase_raises(src_vault, dst_vault):
    with pytest.raises(MergeError, match="destination"):
        merge_vaults(src_vault, PASS_A, dst_vault, "wrong")


def test_merge_result_summary_nothing_changed(dst_vault, tmp_path):
    # src has only KEY2 which already exists in dst and overwrite=False
    src = str(tmp_path / "src2.vault")
    v = Vault.init(src, PASS_A)
    v.set("KEY2", "new")
    v.save()
    result = merge_vaults(src, PASS_A, dst_vault, PASS_B)
    assert result.summary() == "nothing changed"
    assert result.total_changes == 0


def test_merge_result_summary_with_changes(src_vault, dst_vault):
    result = merge_vaults(src_vault, PASS_A, dst_vault, PASS_B)
    assert "added" in result.summary()
    assert result.total_changes == 2
