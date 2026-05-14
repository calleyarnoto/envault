# Importing Secrets from a `.env` File

The `envault import` command lets you bulk-load secrets from an existing
`.env` file into an envault vault without manually running `envault set`
for every key.

## Basic usage

```bash
envault import .env --vault .envault --passphrase "my passphrase"
```

envault reads the file, parses every `KEY=VALUE` pair, and stores each
secret in the vault using the same encryption used by `envault set`.

## Supported syntax

| Syntax | Example |
|--------|--------------------------------------------------|
| Plain assignment | `API_KEY=abc123` |
| Double-quoted value | `SECRET="hello world"` |
| Single-quoted value | `TOKEN='xyz'` |
| `export` prefix | `export DB_URL=postgres://localhost/mydb` |
| Comment lines | `# this line is ignored` |
| Blank lines | *(ignored)* |

## Handling existing keys

By default, keys that **already exist** in the vault are **skipped**:

```
  imported    NEW_KEY
  skipped     EXISTING_KEY (already exists)

Done: 1 imported, 0 overwritten, 1 skipped.
```

To replace existing values, pass `--overwrite`:

```bash
envault import .env --overwrite
```

```
  imported     NEW_KEY
  overwritten  EXISTING_KEY

Done: 1 imported, 1 overwritten, 0 skipped.
```

## Options

| Option | Default | Description |
|-------------|------------|--------------------------------------|
| `--vault` | `.envault` | Path to the vault file |
| `--passphrase` | *(prompt)* | Vault passphrase |
| `--overwrite` | off | Replace existing keys |

## Python API

```python
from pathlib import Path
from envault.import_env import parse_dotenv, import_into_vault

# Parse without writing
secrets = parse_dotenv(Path(".env").read_text())

# Import into vault
report = import_into_vault(
    Path(".envault"),
    passphrase="my passphrase",
    env_source=Path(".env").read_text(),
    overwrite=False,
)
for key, status in report:
    print(f"{key}: {status}")
```

## Security notes

* The `.env` file is read from disk and processed in memory; it is never
  stored in plaintext inside the vault.
* Passphrase handling follows the same key-derivation process as all
  other envault commands (see `envault/crypto.py`).
* Avoid committing `.env` files to version control — use `.gitignore`.
