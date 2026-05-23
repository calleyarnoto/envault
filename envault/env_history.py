"""Track per-key value history inside the vault."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

HISTORY_FILE = ".envault_history.json"
MAX_ENTRIES_PER_KEY = 50


class HistoryError(Exception):
    """Raised on history-related failures."""


@dataclass
class HistoryEntry:
    key: str
    value: str
    timestamp: float = field(default_factory=time.time)
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            key=data["key"],
            value=data["value"],
            timestamp=data["timestamp"],
            note=data.get("note", ""),
        )

    def __repr__(self) -> str:
        return f"<HistoryEntry key={self.key!r} ts={self.timestamp}>"


def _history_path(vault_path: Path) -> Path:
    return vault_path.parent / HISTORY_FILE


def _load_history(vault_path: Path) -> dict:
    p = _history_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_history(vault_path: Path, data: dict) -> None:
    _history_path(vault_path).write_text(json.dumps(data, indent=2))


def record(vault_path: Path, key: str, value: str, note: str = "") -> HistoryEntry:
    """Append a new history entry for *key*."""
    if not vault_path.exists():
        raise HistoryError(f"Vault not found: {vault_path}")
    data = _load_history(vault_path)
    entry = HistoryEntry(key=key, value=value, note=note)
    entries = data.get(key, [])
    entries.append(entry.to_dict())
    data[key] = entries[-MAX_ENTRIES_PER_KEY:]
    _save_history(vault_path, data)
    return entry


def get_history(vault_path: Path, key: str) -> List[HistoryEntry]:
    """Return all recorded history entries for *key*, oldest first."""
    if not vault_path.exists():
        raise HistoryError(f"Vault not found: {vault_path}")
    data = _load_history(vault_path)
    return [HistoryEntry.from_dict(d) for d in data.get(key, [])]


def clear_history(vault_path: Path, key: Optional[str] = None) -> int:
    """Clear history for *key* (or all keys if None). Returns removed count."""
    if not vault_path.exists():
        raise HistoryError(f"Vault not found: {vault_path}")
    data = _load_history(vault_path)
    if key is None:
        count = sum(len(v) for v in data.values())
        _save_history(vault_path, {})
        return count
    entries = data.pop(key, [])
    _save_history(vault_path, data)
    return len(entries)
