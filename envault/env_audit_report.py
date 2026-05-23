"""Generate structured audit reports from the vault audit log."""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.audit import AuditEntry, load_audit_log


class ReportError(Exception):
    """Raised when audit report generation fails."""


@dataclass
class AuditReport:
    entries: List[AuditEntry]
    vault_path: Path
    filter_action: Optional[str] = None
    filter_key: Optional[str] = None

    @property
    def filtered(self) -> List[AuditEntry]:
        result = self.entries
        if self.filter_action:
            result = [e for e in result if e.action == self.filter_action]
        if self.filter_key:
            result = [e for e in result if e.key == self.filter_key]
        return result

    @property
    def total(self) -> int:
        return len(self.filtered)

    def action_counts(self) -> dict:
        return dict(Counter(e.action for e in self.filtered))

    def summary(self) -> str:
        counts = self.action_counts()
        parts = [f"{action}={count}" for action, count in sorted(counts.items())]
        return f"AuditReport(total={self.total}, {', '.join(parts)})"

    def as_text(self) -> str:
        lines = [f"Audit Report — {self.vault_path}", "-" * 40]
        for e in self.filtered:
            key_part = f" [{e.key}]" if e.key else ""
            lines.append(f"{e.timestamp}  {e.action:<12}{key_part}")
        lines.append("-" * 40)
        lines.append(self.summary())
        return "\n".join(lines)

    def as_json(self) -> str:
        return json.dumps([e.to_dict() for e in self.filtered], indent=2)


def build_audit_report(
    vault_path: Path,
    filter_action: Optional[str] = None,
    filter_key: Optional[str] = None,
) -> AuditReport:
    """Load the audit log for *vault_path* and return an AuditReport."""
    if not vault_path.exists():
        raise ReportError(f"Vault not found: {vault_path}")
    entries = load_audit_log(vault_path)
    return AuditReport(
        entries=entries,
        vault_path=vault_path,
        filter_action=filter_action,
        filter_key=filter_key,
    )
