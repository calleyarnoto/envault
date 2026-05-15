"""Tests for envault.env_clone."""

from __future__ import annotations

import pytest

from envault.env_clone import CloneError, clone_vault
from envault.vault import Vault


PASSPHRASE = "hunter2"
DST_PASS = "dst-secret"


@pytest.fixture()
def src_vault(tmp_path):
    path = tmp_path / "src.vault"
    v = Vault(path, PASSPHRASE)
    v.init()
    v.set("ALPHA", "aaa")
    v.set("BETA", "bbb")
    v.set("GAMMA", "ccc")
    return path


def test_clone_all_keys(tmp_path, src_vault):
    dst = tmp_path / "dst.vault"
    count = clone_vault(src_vault, PASSPHRASE, dst, DST_PASS)
    assert count == 3
    v = Vault(dst, DST_PASS)
    assert v.get("ALPHA") == "aaa"
    assert v.get("BETA") == "bbb"
    assert v.get("GAMMA") == "ccc"


def test_clone_subset_of_keys(tmp_path, src_vault):
    dst = tmp_path / "dst.vault"
    count = clone_vault(src_vault, PASSPHRASE, dst, DST_PASS, keys=["ALPHA", "GAMMA"])
    assert count == 2
    v = Vault(dst, DST_PASS)
    assert v.get("ALPHA") == "aaa"
    assert v.get("GAMMA") == "ccc"
    assert v.get("BETA") is None


def test_clone_missing_key_raises(tmp_path, src_vault):
    dst = tmp_path / "dst.vault"
    with pytest.raises(CloneError, match="NOPE"):
        clone_vault(src_vault, PASSPHRASE, dst, DST_PASS, keys=["NOPE"])


def test_clone_missing_src_raises(tmp_path):
    with pytest.raises(CloneError, match="Source vault not found"):
        clone_vault(tmp_path / "ghost.vault", PASSPHRASE, tmp_path / "dst.vault", DST_PASS)


def test_clone_wrong_src_passphrase_raises(tmp_path, src_vault):
    dst = tmp_path / "dst.vault"
    with pytest.raises(CloneError, match="Cannot read source vault"):
        clone_vault(src_vault, "wrong", dst, DST_PASS)


def test_clone_no_overwrite_skips_existing(tmp_path, src_vault):
    dst = tmp_path / "dst.vault"
    # Pre-populate destination with ALPHA=original
    dv = Vault(dst, DST_PASS)
    dv.init()
    dv.set("ALPHA", "original")

    count = clone_vault(src_vault, PASSPHRASE, dst, DST_PASS, overwrite=False)
    # BETA and GAMMA are new; ALPHA is skipped
    assert count == 2
    assert Vault(dst, DST_PASS).get("ALPHA") == "original"


def test_clone_overwrite_replaces_existing(tmp_path, src_vault):
    dst = tmp_path / "dst.vault"
    dv = Vault(dst, DST_PASS)
    dv.init()
    dv.set("ALPHA", "original")

    clone_vault(src_vault, PASSPHRASE, dst, DST_PASS, overwrite=True)
    assert Vault(dst, DST_PASS).get("ALPHA") == "aaa"


def test_clone_creates_dst_vault_if_missing(tmp_path, src_vault):
    dst = tmp_path / "brand_new.vault"
    assert not dst.exists()
    clone_vault(src_vault, PASSPHRASE, dst, DST_PASS)
    assert dst.exists()
