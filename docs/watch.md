# envault watch

The `watch` command polls a vault file at a configurable interval and reacts whenever secrets are added, removed, or changed.

## Usage

```
envault watch start [OPTIONS]
```

### Options

| Option | Default | Description |
|---|---|---|
| `--vault PATH` | `.envault` | Path to the vault file to watch. |
| `--passphrase TEXT` | *(prompted)* | Passphrase used to decrypt the vault. |
| `--interval FLOAT` | `2.0` | Polling interval in seconds. |
| `--exec CMD` | — | Shell command executed whenever a change is detected. |

## Examples

### Basic watch

```bash
envault watch start --vault .envault
```

You will be prompted for the passphrase. The command then polls the vault every 2 seconds and prints a summary whenever secrets change:

```
Watching .envault (interval=2.0s) — press Ctrl+C to stop.
  [+] added:   NEW_TOKEN
  [~] changed: DB_PASSWORD
```

Press **Ctrl+C** to stop watching.

### Trigger a reload command on change

```bash
envault watch start --vault .envault --exec "systemctl reload myapp"
```

Every time a secret changes the shell command is executed via `subprocess.run`.

### Faster polling

```bash
envault watch start --interval 0.5
```

## Python API

```python
from pathlib import Path
from envault.env_watch import watch_vault, WatchEvent

def handle(event: WatchEvent):
    print("added:", event.added)
    print("removed:", event.removed)
    print("changed:", event.changed)

watch_vault(
    Path(".envault"),
    passphrase="my-secret",
    interval=1.0,
    on_change=handle,
)
```

### `WatchEvent`

| Attribute | Type | Description |
|---|---|---|
| `added` | `list[str]` | Keys that appeared since the last poll. |
| `removed` | `list[str]` | Keys that disappeared since the last poll. |
| `changed` | `list[str]` | Keys whose values changed since the last poll. |
| `has_changes` | `bool` | `True` if any of the above lists is non-empty. |

### `watch_vault()`

```python
watch_vault(
    vault_path: Path,
    passphrase: str,
    *,
    interval: float = 2.0,
    max_iterations: int | None = None,
    on_change: Callable[[WatchEvent], None] | None = None,
    shell_cmd: str | None = None,
) -> None
```

Raises `WatchError` if the vault file does not exist or the passphrase is wrong on the first read.
