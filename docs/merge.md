# Vault Merge

The **merge** feature lets you combine secrets from one vault into another.
This is useful when you want to promote secrets between environments (e.g.
`staging` → `production`) or consolidate multiple vaults into one.

## CLI Usage

```bash
envault merge run SRC_VAULT DST_VAULT [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `SRC_VAULT` | Path to the source `.vault` file |
| `DST_VAULT` | Path to the destination `.vault` file |

### Options

| Option | Description |
|--------|-------------|
| `--src-pass TEXT` | Passphrase for the source vault (prompted if omitted) |
| `--dst-pass TEXT` | Passphrase for the destination vault (prompted if omitted) |
| `--key KEY` | Merge only this key (repeatable; merges all when omitted) |
| `--overwrite` | Overwrite keys that already exist in the destination |

## Examples

### Merge all secrets

```bash
envault merge run staging.vault production.vault
```

You will be prompted for both passphrases. Keys that already exist in
`production.vault` are **skipped** unless `--overwrite` is passed.

### Merge a specific key

```bash
envault merge run staging.vault production.vault --key DATABASE_URL
```

### Force overwrite existing keys

```bash
envault merge run staging.vault production.vault --overwrite
```

## Python API

```python
from envault.env_merge import merge_vaults, MergeError

result = merge_vaults(
    "staging.vault", "staging-pass",
    "production.vault", "prod-pass",
    keys=["DATABASE_URL", "REDIS_URL"],
    overwrite=False,
)

print(result.summary())
# e.g. "2 added, 1 skipped"

print(result.added)       # list of newly added keys
print(result.overwritten) # list of overwritten keys
print(result.skipped)     # list of skipped keys
```

## Behaviour

- Keys present in the **source** but absent in the **destination** are always
  added.
- Keys present in **both** vaults are skipped by default; pass `--overwrite`
  to replace them.
- If you specify `--key` values that do not exist in the source vault a
  `MergeError` is raised immediately and no changes are written.
- The destination vault is only written to disk after all keys have been
  processed successfully.
