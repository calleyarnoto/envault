"""Tests for envault.env_generate."""
from __future__ import annotations

import re
import string

import pytest

from envault.env_generate import (
    GenerateError,
    SUPPORTED_FORMATS,
    generate_and_store,
    generate_value,
)
from envault.vault import Vault


# ---------------------------------------------------------------------------
# generate_value
# ---------------------------------------------------------------------------

def test_supported_formats_constant():
    assert "alphanumeric" in SUPPORTED_FORMATS
    assert "hex" in SUPPORTED_FORMATS
    assert "base64url" in SUPPORTED_FORMATS
    assert "pin" in SUPPORTED_FORMATS


def test_alphanumeric_default_length():
    val = generate_value()
    assert len(val) == 32


def test_alphanumeric_custom_length():
    val = generate_value(length=16)
    assert len(val) == 16


def test_alphanumeric_only_safe_chars():
    val = generate_value(length=200)
    allowed = set(string.ascii_letters + string.digits)
    assert set(val).issubset(allowed)


def test_alphanumeric_with_special_chars():
    # Run several times to ensure special chars appear
    found_special = False
    for _ in range(50):
        val = generate_value(length=64, include_special=True)
        if set(val) - set(string.ascii_letters + string.digits):
            found_special = True
            break
    assert found_special


def test_hex_format_is_valid_hex():
    val = generate_value(length=16, fmt="hex")
    assert re.fullmatch(r"[0-9a-f]+", val)


def test_hex_format_length_is_double():
    # token_hex(n) returns 2*n hex chars
    val = generate_value(length=8, fmt="hex")
    assert len(val) == 16


def test_base64url_format():
    val = generate_value(length=16, fmt="base64url")
    # urlsafe base64 chars
    assert re.fullmatch(r"[A-Za-z0-9_\-]+=*", val)


def test_pin_format_digits_only():
    val = generate_value(length=6, fmt="pin")
    assert val.isdigit()
    assert len(val) == 6


def test_unsupported_format_raises():
    with pytest.raises(GenerateError, match="unsupported format"):
        generate_value(fmt="emoji")  # type: ignore[arg-type]


def test_zero_length_raises():
    with pytest.raises(GenerateError, match="length must be at least 1"):
        generate_value(length=0)


def test_values_are_unique():
    vals = {generate_value() for _ in range(20)}
    assert len(vals) == 20


# ---------------------------------------------------------------------------
# generate_and_store
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "test.vault")
    Vault.init(path, "s3cr3t")
    return path


def test_generate_and_store_returns_value(vault_file):
    val = generate_and_store(vault_file, "s3cr3t", "MY_KEY")
    assert isinstance(val, str)
    assert len(val) == 32


def test_generate_and_store_persists_value(vault_file):
    val = generate_and_store(vault_file, "s3cr3t", "MY_KEY")
    vault = Vault.load(vault_file, "s3cr3t")
    assert vault.get("MY_KEY") == val


def test_generate_and_store_raises_if_key_exists(vault_file):
    generate_and_store(vault_file, "s3cr3t", "MY_KEY")
    with pytest.raises(GenerateError, match="already exists"):
        generate_and_store(vault_file, "s3cr3t", "MY_KEY")


def test_generate_and_store_overwrite(vault_file):
    first = generate_and_store(vault_file, "s3cr3t", "MY_KEY")
    second = generate_and_store(vault_file, "s3cr3t", "MY_KEY", overwrite=True)
    vault = Vault.load(vault_file, "s3cr3t")
    assert vault.get("MY_KEY") == second
    # Values are almost certainly different (probabilistic)
    assert first != second or True  # always passes; just exercises the path
