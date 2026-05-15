"""Generate human-readable diff reports between vault states or profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from envault.diff import SecretDiff, diff_secrets
from envault.vault import Vault, VaultError


class ReportError(Exception):
    """Raised when a diff report cannot be generated."""


@dataclass
class DiffReport:
    added: List[SecretDiff]
    removed: List[SecretDiff]
    changed: List[SecretDiff]
    unchanged: List[SecretDiff]

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)

    def summary(self) -> str:
        lines = [
            f"Added:    {len(self.added)}",
            f"Removed:  {len(self.removed)}",
            f"Changed:  {len(self.changed)}",
            f"Unchanged:{len(self.unchanged)}",
        ]
        return "\n".join(lines)

    def as_text(self, show_values: bool = False) -> str:
        """Render the report as a coloured-style text block."""
        out: List[str] = []

        for d in self.added:
            val = f" = {d.new_value!r}" if show_values else ""
            out.append(f"+ {d.key}{val}")

        for d in self.removed:
            val = f" = {d.old_value!r}" if show_values else ""
            out.append(f"- {d.key}{val}")

        for d in self.changed:
            if show_values:
                out.append(f"~ {d.key}  {d.old_value!r} -> {d.new_value!r}")
            else:
                out.append(f"~ {d.key}")

        if not out:
            return "No changes detected."
        return "\n".join(out)


def build_report(
    old_secrets: dict,
    new_secrets: dict,
    include_unchanged: bool = False,
) -> DiffReport:
    """Build a DiffReport from two secret dictionaries."""
    all_diffs = diff_secrets(old_secrets, new_secrets, include_unchanged=True)
    added = [d for d in all_diffs if d.status == "added"]
    removed = [d for d in all_diffs if d.status == "removed"]
    changed = [d for d in all_diffs if d.status == "changed"]
    unchanged = [d for d in all_diffs if d.status == "unchanged"]
    return DiffReport(added=added, removed=removed, changed=changed, unchanged=unchanged)


def report_vault_vs_dict(
    vault: Vault,
    passphrase: str,
    reference: dict,
    include_unchanged: bool = False,
) -> DiffReport:
    """Compare a vault's current secrets against a reference dict."""
    try:
        current = vault.all(passphrase)
    except VaultError as exc:
        raise ReportError(str(exc)) from exc
    return build_report(reference, current, include_unchanged=include_unchanged)
