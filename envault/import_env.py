"""Import secrets from existing .env files into the vault."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

from envault.vault import Vault, VaultError

__all__ = ["ImportError", "parse_dotenv", "import_into_vault"]

_LINE_RE = re.compile(
    r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$"
)


class ImportError(Exception):  # noqa: A001  (shadows built-in intentionally)
    """Raised when an import operation fails."""


def parse_dotenv(source: str) -> Dict[str, str]:
    """Parse a .env-formatted string and return a dict of key/value pairs.

    - Lines starting with ``#`` are treated as comments.
    - Surrounding single or double quotes are stripped from values.
    - ``export KEY=VALUE`` syntax is supported.
    """
    result: Dict[str, str] = {}
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _LINE_RE.match(stripped)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        # Strip matching surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def import_into_vault(
    vault_path: Path,
    passphrase: str,
    env_source: str,
    *,
    overwrite: bool = False,
) -> List[Tuple[str, str]]:
    """Import key/value pairs from *env_source* into the vault.

    Returns a list of ``(key, status)`` tuples where *status* is one of
    ``'imported'``, ``'skipped'`` (key already exists and *overwrite* is
    ``False``), or ``'overwritten'``.

    Raises :class:`ImportError` if the vault file does not exist.
    """
    if not vault_path.exists():
        raise ImportError(f"Vault not found: {vault_path}")

    parsed = parse_dotenv(env_source)
    if not parsed:
        return []

    vault = Vault.load(vault_path, passphrase)
    report: List[Tuple[str, str]] = []

    for key, value in parsed.items():
        existing = vault.get(key)
        if existing is not None and not overwrite:
            report.append((key, "skipped"))
            continue
        status = "overwritten" if existing is not None else "imported"
        vault.set(key, value)
        report.append((key, status))

    vault.save(passphrase)
    return report
