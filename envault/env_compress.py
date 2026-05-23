"""Vault compression: compress and decompress vault files to reduce storage footprint."""

from __future__ import annotations

import gzip
import shutil
from pathlib import Path

COMPRESSED_SUFFIX = ".gz"


class CompressError(Exception):
    """Raised when a compress/decompress operation fails."""


def compress_vault(vault_path: str | Path, *, remove_original: bool = False) -> Path:
    """Compress *vault_path* with gzip and return the compressed file path.

    Parameters
    ----------
    vault_path:
        Path to the plaintext (or encrypted) vault file.
    remove_original:
        When *True* the source file is deleted after successful compression.

    Returns
    -------
    Path
        Path to the newly created ``.gz`` file.
    """
    src = Path(vault_path)
    if not src.exists():
        raise CompressError(f"Vault file not found: {src}")

    dest = src.with_suffix(src.suffix + COMPRESSED_SUFFIX)
    if dest.exists():
        raise CompressError(f"Compressed file already exists: {dest}")

    try:
        with src.open("rb") as f_in, gzip.open(dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    except OSError as exc:
        raise CompressError(f"Compression failed: {exc}") from exc

    if remove_original:
        src.unlink()

    return dest


def decompress_vault(compressed_path: str | Path, *, remove_compressed: bool = False) -> Path:
    """Decompress a gzip-compressed vault file and return the decompressed file path.

    Parameters
    ----------
    compressed_path:
        Path to the ``.gz`` vault file.
    remove_compressed:
        When *True* the ``.gz`` source file is deleted after successful decompression.

    Returns
    -------
    Path
        Path to the decompressed vault file.
    """
    src = Path(compressed_path)
    if not src.exists():
        raise CompressError(f"Compressed file not found: {src}")

    if src.suffix != COMPRESSED_SUFFIX:
        raise CompressError(f"Expected a '{COMPRESSED_SUFFIX}' file, got: {src.name}")

    dest = src.with_suffix("")  # strip .gz
    if dest.exists():
        raise CompressError(f"Decompressed file already exists: {dest}")

    try:
        with gzip.open(src, "rb") as f_in, dest.open("wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    except (OSError, gzip.BadGzipFile) as exc:
        raise CompressError(f"Decompression failed: {exc}") from exc

    if remove_compressed:
        src.unlink()

    return dest


def compressed_size_info(vault_path: str | Path) -> dict:
    """Return a dict with original size, compressed size, and ratio for *vault_path*."""
    src = Path(vault_path)
    if not src.exists():
        raise CompressError(f"Vault file not found: {src}")

    original_bytes = src.stat().st_size
    compressed_path = compress_vault(src)
    try:
        compressed_bytes = compressed_path.stat().st_size
    finally:
        compressed_path.unlink(missing_ok=True)

    ratio = (1 - compressed_bytes / original_bytes) * 100 if original_bytes else 0.0
    return {
        "original_bytes": original_bytes,
        "compressed_bytes": compressed_bytes,
        "ratio_pct": round(ratio, 2),
    }
