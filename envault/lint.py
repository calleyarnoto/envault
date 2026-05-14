"""Lint secrets in a vault against configurable rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envault.vault import Vault, VaultError


class LintError(Exception):
    """Raised when the vault cannot be loaded for linting."""


@dataclass
class LintIssue:
    key: str
    rule: str
    message: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"LintIssue(key={self.key!r}, rule={self.rule!r})"


# ---------------------------------------------------------------------------
# Built-in rules
# ---------------------------------------------------------------------------

_WEAK_PATTERNS = [
    re.compile(r"^(password|secret|token|key)$", re.IGNORECASE),
    re.compile(r"^(123|abc|test|demo|example)", re.IGNORECASE),
]


def _rule_empty_value(key: str, value: str) -> Optional[LintIssue]:
    if not value.strip():
        return LintIssue(key, "empty_value", f"'{key}' has an empty value.")
    return None


def _rule_weak_value(key: str, value: str) -> Optional[LintIssue]:
    for pat in _WEAK_PATTERNS:
        if pat.match(value):
            return LintIssue(
                key, "weak_value", f"'{key}' looks like a placeholder or weak secret."
            )
    return None


def _rule_short_value(key: str, value: str, min_len: int = 8) -> Optional[LintIssue]:
    if 0 < len(value) < min_len:
        return LintIssue(
            key,
            "short_value",
            f"'{key}' value is shorter than {min_len} characters.",
        )
    return None


def _rule_key_naming(key: str, value: str) -> Optional[LintIssue]:
    if not re.match(r"^[A-Z][A-Z0-9_]*$", key):
        return LintIssue(
            key,
            "key_naming",
            f"'{key}' does not follow UPPER_SNAKE_CASE convention.",
        )
    return None


_RULES = [_rule_empty_value, _rule_weak_value, _rule_short_value, _rule_key_naming]


def lint_vault(vault_path: str, passphrase: str) -> List[LintIssue]:
    """Return a list of LintIssue objects found in the vault."""
    try:
        vault = Vault.load(vault_path, passphrase)
    except VaultError as exc:
        raise LintError(str(exc)) from exc

    issues: List[LintIssue] = []
    for key, value in vault.secrets.items():
        for rule_fn in _RULES:
            issue = rule_fn(key, value)
            if issue:
                issues.append(issue)
    return issues
