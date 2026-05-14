"""Environment variable health checks for envault secrets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envault.vault import Vault, VaultError


class CheckError(Exception):
    """Raised when a health check operation fails."""


@dataclass
class CheckResult:
    key: str
    status: str          # 'ok' | 'missing' | 'expired' | 'invalid_format'
    message: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return f"CheckResult(key={self.key!r}, status={self.status!r}, message={self.message!r})"


# Optional regex pattern map: key glob -> compiled pattern
_FORMAT_RULES: dict[str, re.Pattern] = {
    "*_URL": re.compile(r"^https?://"),
    "*_EMAIL": re.compile(r"^[^@]+@[^@]+\.[^@]+$"),
    "*_PORT": re.compile(r"^\d{1,5}$"),
}


def _match_format_rule(key: str, value: str) -> Optional[str]:
    """Return a failure message if *value* violates a known format rule, else None."""
    import fnmatch

    for pattern, regex in _FORMAT_RULES.items():
        if fnmatch.fnmatch(key.upper(), pattern):
            if not regex.match(value):
                return f"value does not match expected format for '{pattern}'"
    return None


def check_secrets(
    vault: Vault,
    passphrase: str,
    required_keys: Optional[List[str]] = None,
    check_format: bool = True,
) -> List[CheckResult]:
    """Run health checks on vault secrets.

    Args:
        vault: An open :class:`~envault.vault.Vault` instance.
        passphrase: Passphrase used to decrypt secrets.
        required_keys: If provided, keys that *must* exist in the vault.
        check_format: Whether to apply naming-convention format rules.

    Returns:
        List of :class:`CheckResult` objects, one per issue found.
        An empty list means everything is healthy.
    """
    try:
        secrets = vault.list_keys()
    except VaultError as exc:
        raise CheckError(f"Could not access vault: {exc}") from exc

    results: List[CheckResult] = []

    # 1. Required-key presence check
    if required_keys:
        for key in required_keys:
            if key not in secrets:
                results.append(CheckResult(key=key, status="missing",
                                           message="required key not found in vault"))

    # 2. Format checks on existing secrets
    if check_format:
        for key in secrets:
            try:
                value = vault.get(key, passphrase)
            except VaultError as exc:
                results.append(CheckResult(key=key, status="invalid_format",
                                           message=f"could not decrypt: {exc}"))
                continue

            failure = _match_format_rule(key, value)
            if failure:
                results.append(CheckResult(key=key, status="invalid_format",
                                           message=failure))

    return results
