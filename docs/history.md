# Secret Value History

envault can record the history of values assigned to each secret key, giving you an audit trail of changes over time.

## Overview

Each time a value is recorded (manually or via integration), an entry is appended to a local `.envault_history.json` file stored alongside the vault. Entries are capped at **50 per key** (oldest are dropped).

## Python API

```python
from envault.env_history import record, get_history, clear_history
from pathlib import Path

vault = Path(".envault")

# Record a value change
entry = record(vault, "DB_URL", "postgres://prod/db", note="promoted to prod")
print(entry)  # <HistoryEntry key='DB_URL' ts=1718000000.0>

# Retrieve full history for a key
for e in get_history(vault, "DB_URL"):
    print(e.timestamp, e.value, e.note)

# Clear history for one key
removed = clear_history(vault, "DB_URL")
print(f"Removed {removed} entries")

# Clear all history
clear_history(vault)
```

## CLI Usage

### List history for a key

```bash
envault history list DB_URL
```

Output:
```
History for 'DB_URL' (2 entries):
    1. [2024-06-10 09:00:00] 'postgres://localhost/db'  # initial set
    2. [2024-06-11 14:32:01] 'postgres://prod/db'  # promoted to prod
```

### Manually record a value

```bash
envault history record DB_URL "postgres://prod/db" --note "promoted to prod"
```

### Clear history

```bash
# Clear a specific key
envault history clear DB_URL --yes

# Clear all history
envault history clear --yes
```

## HistoryEntry Fields

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str` | The secret key name |
| `value` | `str` | The recorded value |
| `timestamp` | `float` | Unix timestamp of the entry |
| `note` | `str` | Optional free-text note |

## Storage

History is stored in `.envault_history.json` next to the vault file. This file should be added to `.gitignore` to avoid leaking secret values.

```gitignore
.envault_history.json
```

## Limits

- Maximum **50 entries per key** (configurable via `MAX_ENTRIES_PER_KEY` in `env_history.py`).
- Entries beyond the cap are dropped from the oldest end.
