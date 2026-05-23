"""Tests for envault.env_compress."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from envault.env_compress import (
    COMPRESSED_SUFFIX,
    CompressError,
    compress_vault,
    compressed_size_info,
    decompress_vault,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    """A small fake vault JSON file."""
    p = tmp_path / "vault.env"
    data = {"KEY_A": "alpha", "KEY_B": "beta", "KEY_C": "gamma" * 20}
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# compress_vault
# ---------------------------------------------------------------------------

def test_compress_returns_gz_path(vault_file: Path) -> None:
    result = compress_vault(vault_file)
    assert result.suffix == COMPRESSED_SUFFIX
    assert result.name == vault_file.name + COMPRESSED_SUFFIX


def test_compress_creates_file(vault_file: Path) -> None:
    result = compress_vault(vault_file)
    assert result.exists()


def test_compress_original_still_exists_by_default(vault_file: Path) -> None:
    compress_vault(vault_file)
    assert vault_file.exists()


def test_compress_remove_original_flag(vault_file: Path) -> None:
    compress_vault(vault_file, remove_original=True)
    assert not vault_file.exists()


def test_compress_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(CompressError, match="not found"):
        compress_vault(tmp_path / "ghost.env")


def test_compress_already_exists_raises(vault_file: Path) -> None:
    compress_vault(vault_file)  # first call succeeds
    with pytest.raises(CompressError, match="already exists"):
        compress_vault(vault_file)  # second call must raise


# ---------------------------------------------------------------------------
# decompress_vault
# ---------------------------------------------------------------------------

def test_decompress_restores_content(vault_file: Path) -> None:
    original_text = vault_file.read_text()
    gz_path = compress_vault(vault_file)
    vault_file.unlink()  # remove original so decompress can write it
    restored = decompress_vault(gz_path)
    assert restored.read_text() == original_text


def test_decompress_returns_path_without_gz_suffix(vault_file: Path) -> None:
    gz_path = compress_vault(vault_file)
    vault_file.unlink()
    restored = decompress_vault(gz_path)
    assert restored.suffix != COMPRESSED_SUFFIX


def test_decompress_remove_compressed_flag(vault_file: Path) -> None:
    gz_path = compress_vault(vault_file)
    vault_file.unlink()
    decompress_vault(gz_path, remove_compressed=True)
    assert not gz_path.exists()


def test_decompress_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(CompressError, match="not found"):
        decompress_vault(tmp_path / "ghost.env.gz")


def test_decompress_wrong_suffix_raises(vault_file: Path) -> None:
    with pytest.raises(CompressError, match="Expected a"):
        decompress_vault(vault_file)  # not a .gz file


def test_decompress_destination_exists_raises(vault_file: Path) -> None:
    gz_path = compress_vault(vault_file)
    # vault_file still exists → destination conflict
    with pytest.raises(CompressError, match="already exists"):
        decompress_vault(gz_path)


# ---------------------------------------------------------------------------
# compressed_size_info
# ---------------------------------------------------------------------------

def test_size_info_keys_present(vault_file: Path) -> None:
    info = compressed_size_info(vault_file)
    assert {"original_bytes", "compressed_bytes", "ratio_pct"} == set(info.keys())


def test_size_info_original_bytes_correct(vault_file: Path) -> None:
    info = compressed_size_info(vault_file)
    assert info["original_bytes"] == vault_file.stat().st_size


def test_size_info_no_leftover_gz_file(vault_file: Path) -> None:
    compressed_size_info(vault_file)
    gz = vault_file.with_suffix(vault_file.suffix + COMPRESSED_SUFFIX)
    assert not gz.exists()


def test_size_info_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(CompressError, match="not found"):
        compressed_size_info(tmp_path / "ghost.env")
