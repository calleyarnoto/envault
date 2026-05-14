"""Tests for envault.share."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.share import (
    ShareError,
    create_share,
    read_share,
    import_share,
)


PASS = "vault-pass"
SHARE_PASS = "share-pass"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    v = Vault(path)
    v.init(PASS)
    v.set(PASS, "DB_URL", "postgres://localhost/db")
    v.set(PASS, "API_KEY", "supersecret")
    v.set(PASS, "DEBUG", "true")
    return path


def test_create_share_returns_string(vault_file):
    bundle = create_share(vault_file, PASS, ["DB_URL"], SHARE_PASS)
    assert isinstance(bundle, str)
    assert len(bundle) > 0


def test_create_share_multiple_keys(vault_file):
    bundle = create_share(vault_file, PASS, ["DB_URL", "API_KEY"], SHARE_PASS)
    secrets = read_share(bundle, SHARE_PASS)
    assert secrets == {"DB_URL": "postgres://localhost/db", "API_KEY": "supersecret"}


def test_create_share_missing_key_raises(vault_file):
    with pytest.raises(ShareError, match="Keys not found"):
        create_share(vault_file, PASS, ["MISSING_KEY"], SHARE_PASS)


def test_create_share_wrong_passphrase_raises(vault_file):
    with pytest.raises(ShareError, match="Cannot open vault"):
        create_share(vault_file, "wrong-pass", ["DB_URL"], SHARE_PASS)


def test_read_share_wrong_passphrase_raises(vault_file):
    bundle = create_share(vault_file, PASS, ["DB_URL"], SHARE_PASS)
    with pytest.raises(ShareError, match="Failed to decrypt"):
        read_share(bundle, "wrong-share-pass")


def test_read_share_corrupted_bundle_raises():
    with pytest.raises(ShareError):
        read_share("not-a-valid-bundle", SHARE_PASS)


def test_import_share_writes_secrets(vault_file, tmp_path):
    bundle = create_share(vault_file, PASS, ["DB_URL", "API_KEY"], SHARE_PASS)

    dest = tmp_path / "dest.vault"
    dv = Vault(dest)
    dv.init(PASS)

    count = import_share(bundle, SHARE_PASS, dest, PASS)
    assert count == 2

    dv.load(PASS)
    assert dv.secrets["DB_URL"] == "postgres://localhost/db"
    assert dv.secrets["API_KEY"] == "supersecret"


def test_import_share_conflict_raises(vault_file, tmp_path):
    bundle = create_share(vault_file, PASS, ["DB_URL"], SHARE_PASS)

    dest = tmp_path / "dest.vault"
    dv = Vault(dest)
    dv.init(PASS)
    dv.set(PASS, "DB_URL", "existing-value")

    with pytest.raises(ShareError, match="already exist"):
        import_share(bundle, SHARE_PASS, dest, PASS)


def test_import_share_overwrite_allowed(vault_file, tmp_path):
    bundle = create_share(vault_file, PASS, ["DB_URL"], SHARE_PASS)

    dest = tmp_path / "dest.vault"
    dv = Vault(dest)
    dv.init(PASS)
    dv.set(PASS, "DB_URL", "old-value")

    count = import_share(bundle, SHARE_PASS, dest, PASS, overwrite=True)
    assert count == 1
    dv.load(PASS)
    assert dv.secrets["DB_URL"] == "postgres://localhost/db"
