"""Secret value generator for envault."""
from __future__ import annotations

import random
import secrets
import string
from typing import Literal

from envault.vault import Vault, VaultError

GenerateFormat = Literal["alphanumeric", "hex", "base64url", "pin"]

SUPPORTED_FORMATS: tuple[GenerateFormat, ...] = (
    "alphanumeric",
    "hex",
    "base64url",
    "pin",
)

_ALPHANUMERIC = string.ascii_letters + string.digits
_ALPHANUMERIC_SPECIAL = _ALPHANUMERIC + string.punctuation.replace('"', "").replace("'", "")


class GenerateError(Exception):
    """Raised when secret generation fails."""


def generate_value(
    length: int = 32,
    fmt: GenerateFormat = "alphanumeric",
    *,
    include_special: bool = False,
) -> str:
    """Return a cryptographically random secret string.

    Args:
        length: Number of characters (or bytes for hex/base64url).
        fmt: Output format.
        include_special: Include punctuation (alphanumeric only).

    Returns:
        Generated secret string.
    """
    if length < 1:
        raise GenerateError("length must be at least 1")
    if fmt not in SUPPORTED_FORMATS:
        raise GenerateError(
            f"unsupported format {fmt!r}; choose from {SUPPORTED_FORMATS}"
        )

    if fmt == "hex":
        return secrets.token_hex(length)
    if fmt == "base64url":
        return secrets.token_urlsafe(length)
    if fmt == "pin":
        return "".join(secrets.choice(string.digits) for _ in range(length))
    # alphanumeric
    alphabet = _ALPHANUMERIC_SPECIAL if include_special else _ALPHANUMERIC
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_and_store(
    vault_path: str,
    passphrase: str,
    key: str,
    length: int = 32,
    fmt: GenerateFormat = "alphanumeric",
    *,
    include_special: bool = False,
    overwrite: bool = False,
) -> str:
    """Generate a secret and store it in the vault.

    Returns the generated value.
    """
    vault = Vault.load(vault_path, passphrase)
    if key in vault.list() and not overwrite:
        raise GenerateError(
            f"key {key!r} already exists; pass overwrite=True to replace it"
        )
    value = generate_value(length=length, fmt=fmt, include_special=include_special)
    vault.set(key, value)
    vault.save()
    return value
