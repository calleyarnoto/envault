"""Search secrets within a vault by key pattern or value substring."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from typing import List, Optional

from envault.vault import Vault, VaultError


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchResult:
    key: str
    value: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"SearchResult(key={self.key!r}, value={self.value!r})"


def search_secrets(
    vault: Vault,
    passphrase: str,
    *,
    key_pattern: Optional[str] = None,
    value_substring: Optional[str] = None,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Return secrets whose key matches *key_pattern* (glob) and/or whose
    value contains *value_substring*.

    At least one of *key_pattern* or *value_substring* must be provided.

    Parameters
    ----------
    vault:
        An already-loaded :class:`~envault.vault.Vault` instance.
    passphrase:
        Passphrase used to decrypt individual secret values.
    key_pattern:
        Optional glob pattern (e.g. ``"AWS_*"``) matched against secret keys.
    value_substring:
        Optional substring searched for inside decrypted values.
    case_sensitive:
        When *False* (default) both key and value comparisons ignore case.
    """
    if key_pattern is None and value_substring is None:
        raise SearchError(
            "Provide at least one of 'key_pattern' or 'value_substring'."
        )

    secrets = vault.list_keys()
    results: List[SearchResult] = []

    for key in sorted(secrets):
        # --- key filter ---
        if key_pattern is not None:
            candidate = key if case_sensitive else key.lower()
            pattern = key_pattern if case_sensitive else key_pattern.lower()
            if not fnmatch.fnmatch(candidate, pattern):
                continue

        # --- value filter ---
        try:
            value = vault.get(key, passphrase)
        except VaultError as exc:
            raise SearchError(f"Could not decrypt '{key}': {exc}") from exc

        if value_substring is not None:
            needle = value_substring if case_sensitive else value_substring.lower()
            haystack = value if case_sensitive else value.lower()
            if needle not in haystack:
                continue

        results.append(SearchResult(key=key, value=value))

    return results
