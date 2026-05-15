# Secret Rename

envault lets you rename a secret key inside a vault while preserving its
value, tags, and TTL expiry.

## Python API

```python
from pathlib import Path
from envault.env_rename import rename_secret, RenameError

rename_secret(
    vault_path=Path(".envault/myproject.vault"),
    passphrase="my-passphrase",
    old_key="API_KEY",
    new_key="API_TOKEN",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `vault_path` | `Path` | Path to the `.vault` file |
| `passphrase` | `str` | Vault passphrase |
| `old_key` | `str` | Existing key to rename |
| `new_key` | `str` | Target key name |
| `overwrite` | `bool` | Replace `new_key` if it already exists (default `False`) |

### Return value

`None` — the vault file is updated in place.

## Behaviour

- The secret **value** is carried over unchanged.
- Any **tags** attached to `old_key` are moved to `new_key`.
- Any **TTL** expiry set on `old_key` is moved to `new_key`.
- Audit log entries are **not** back-dated; a new `set` entry for `new_key`
  and a `delete` entry for `old_key` are appended by the underlying
  `Vault` operations.

## Errors

| Exception | Reason |
|-----------|--------|
| `RenameError` | `old_key` missing, `new_key` already exists without `overwrite`, or keys are identical |
| `VaultError` | I/O or decryption failure |

## Example: safe rename with overwrite guard

```python
try:
    rename_secret(vault_path, passphrase, "OLD_NAME", "NEW_NAME")
except RenameError as exc:
    print(f"Rename failed: {exc}")
```

## Example: force overwrite

```python
rename_secret(
    vault_path, passphrase,
    old_key="STAGING_TOKEN",
    new_key="PROD_TOKEN",
    overwrite=True,
)
```
