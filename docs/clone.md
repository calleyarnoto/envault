# Vault Cloning

The **clone** feature lets you copy secrets from one envault vault into another,
optionally filtering to a subset of keys and choosing whether to overwrite
existing secrets in the destination.

## Python API

```python
from pathlib import Path
from envault.env_clone import clone_vault

written = clone_vault(
    src_path=Path(".envault/production.vault"),
    src_passphrase="prod-pass",
    dst_path=Path(".envault/staging.vault"),
    dst_passphrase="staging-pass",
)
print(f"{written} secrets cloned.")
```

### Selective clone

Pass a list of key names to copy only those secrets:

```python
clone_vault(
    src_path=Path("prod.vault"),
    src_passphrase="prod-pass",
    dst_path=Path("staging.vault"),
    dst_passphrase="staging-pass",
    keys=["DATABASE_URL", "REDIS_URL"],
)
```

### Overwrite behaviour

By default existing keys in the destination vault are **skipped** (not
overwritten).  Pass `overwrite=True` to replace them:

```python
clone_vault(
    src_path=Path("prod.vault"),
    src_passphrase="prod-pass",
    dst_path=Path("staging.vault"),
    dst_passphrase="staging-pass",
    overwrite=True,
)
```

## Error handling

| Situation | Exception raised |
|---|---|
| Source vault file not found | `CloneError` |
| Wrong source passphrase | `CloneError` |
| Wrong destination passphrase | `CloneError` |
| Requested key missing from source | `CloneError` |

All exceptions are subclasses of `CloneError` from `envault.env_clone`.

## Notes

- If the destination vault does not yet exist it is **created automatically**.
- The destination passphrase is completely independent of the source passphrase.
- Cloning does **not** copy TTL metadata, tags, or audit history — only the
  raw secret values.
