# Vault Backup & Restore

`envault backup` lets you create point-in-time copies of your vault file and
restore them later — useful before a bulk import, rotation, or deployment.

---

## Commands

### `envault backup create`

Create a compressed (gzip) backup of the vault.

```bash
envault backup create
# Backup created: .envault_backups/.envault_1718000000.bak.gz
```

#### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--vault PATH` | `.envault` | Path to the vault file. |
| `--label TEXT` | *(empty)* | Human-readable label embedded in the filename. |
| `--no-compress` | off | Skip gzip compression. |

#### Example — labelled backup before a deploy

```bash
envault backup create --label pre-deploy
# Backup created: .envault_backups/.envault_pre-deploy_1718000000.bak.gz
```

---

### `envault backup list`

List all backups for the current vault, sorted oldest-first.

```bash
envault backup list
# .envault_backups/.envault_1718000000.bak.gz
# .envault_backups/.envault_pre-deploy_1718001234.bak.gz
```

---

### `envault backup restore`

Restore a vault from a backup file.

```bash
envault backup restore .envault_backups/.envault_1718000000.bak.gz
```

By default the command refuses to overwrite an existing vault.
Pass `--overwrite` to replace it:

```bash
envault backup restore .envault_backups/.envault_1718000000.bak.gz --overwrite
```

#### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--vault PATH` | `.envault` | Destination vault path. |
| `--overwrite` | off | Replace the vault if it already exists. |

---

## Storage layout

Backups are stored in `.envault_backups/` next to the vault file.
Add this directory to `.gitignore` to avoid committing backups:

```gitignore
.envault_backups/
```

---

## Compressed vs uncompressed

By default backups are gzip-compressed (`.bak.gz`). Use `--no-compress` when
you need a plain-text copy for inspection or external tooling.
