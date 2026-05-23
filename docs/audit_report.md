# Audit Report

The `env_audit_report` module provides structured reporting over a vault's audit log.
It lets you filter, summarise, and export audit history in text or JSON format.

## Quick Start

```python
from pathlib import Path
from envault.env_audit_report import build_audit_report

report = build_audit_report(Path("my-project.vault"))
print(report.as_text())
```

## Filtering

### By action

```python
report = build_audit_report(vault_path, filter_action="set")
```

Common actions: `init`, `set`, `get`, `delete`, `rotate`.

### By key

```python
report = build_audit_report(vault_path, filter_key="DATABASE_URL")
```

### Combined

```python
report = build_audit_report(
    vault_path,
    filter_action="set",
    filter_key="API_KEY",
)
```

## Output Formats

### Plain text

```python
print(report.as_text())
```

Example output:

```
Audit Report — /home/user/project.vault
----------------------------------------
2024-06-01T12:00:00  init
2024-06-01T12:01:00  set          [DATABASE_URL]
2024-06-01T12:02:00  set          [API_KEY]
2024-06-01T12:03:00  get          [DATABASE_URL]
----------------------------------------
AuditReport(total=4, get=1, init=1, set=2)
```

### JSON

```python
import json
data = json.loads(report.as_json())
```

Each entry mirrors the `AuditEntry.to_dict()` schema:

```json
[
  {"timestamp": "2024-06-01T12:00:00", "action": "init", "key": null},
  {"timestamp": "2024-06-01T12:01:00", "action": "set",  "key": "DATABASE_URL"}
]
```

## API Reference

### `build_audit_report(vault_path, filter_action=None, filter_key=None) -> AuditReport`

Loads the audit log from *vault_path* and returns an `AuditReport`.
Raises `ReportError` if the vault file does not exist.

### `AuditReport`

| Attribute / Method | Description |
|--------------------|-------------|
| `filtered`         | List of `AuditEntry` objects after applying filters |
| `total`            | Number of entries in `filtered` |
| `action_counts()`  | `dict` mapping action name → count |
| `summary()`        | One-line human-readable summary |
| `as_text()`        | Multi-line plain-text report |
| `as_json()`        | JSON string of filtered entries |
