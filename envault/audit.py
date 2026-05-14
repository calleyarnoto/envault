"""Audit log for envault — tracks vault operations with timestamps."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_LOG_FILENAME = ".envault_audit.json"


class AuditEntry:
    """A single audit log entry."""

    def __init__(self, action: str, key: Optional[str], user: str, timestamp: str):
        self.action = action
        self.key = key
        self.user = user
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "key": self.key,
            "user": self.user,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            action=data["action"],
            key=data.get("key"),
            user=data["user"],
            timestamp=data["timestamp"],
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"AuditEntry(action={self.action!r}, key={self.key!r}, user={self.user!r})"


def _current_user() -> str:
    """Return the current OS user or 'unknown'."""
    return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_audit_log(vault_path: Path) -> List[AuditEntry]:
    """Load existing audit entries from disk."""
    log_path = vault_path.parent / AUDIT_LOG_FILENAME
    if not log_path.exists():
        return []
    with log_path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return [AuditEntry.from_dict(entry) for entry in raw]


def append_audit_entry(
    vault_path: Path,
    action: str,
    key: Optional[str] = None,
    user: Optional[str] = None,
) -> AuditEntry:
    """Append a new audit entry and persist the log."""
    entries = load_audit_log(vault_path)
    entry = AuditEntry(
        action=action,
        key=key,
        user=user or _current_user(),
        timestamp=_now_iso(),
    )
    entries.append(entry)
    log_path = vault_path.parent / AUDIT_LOG_FILENAME
    with log_path.open("w", encoding="utf-8") as fh:
        json.dump([e.to_dict() for e in entries], fh, indent=2)
    return entry
