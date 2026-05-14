# Secret TTL (Time-to-Live)

envault supports setting an expiry on individual secrets. Once a secret's TTL
elapses it is considered *expired* and can be automatically purged from the
vault.

---

## Concepts

| Term | Meaning |
|------|---------|
| **TTL** | Duration in seconds until a secret expires |
| **Expiry timestamp** | Unix epoch time at which the secret becomes stale |
| **Purge** | Permanently delete all expired secrets from the vault |

TTL metadata is stored in a sidecar file (`.envault_ttl.json`) next to the
vault file. It is **not** encrypted because it contains only timestamps, not
secret values.

---

## Python API

```python
from pathlib import Path
from envault.ttl import set_ttl, get_ttl, remove_ttl, expired_keys, purge_expired

vault_path = Path(".envault")

# Expire DB_URL in 24 hours
expiry = set_ttl(vault_path, "DB_URL", seconds=86400)
print(f"DB_URL expires at {expiry}")

# Check the expiry timestamp
ts = get_ttl(vault_path, "DB_URL")  # float or None

# List all keys that have already expired
stale = expired_keys(vault_path)

# Remove the TTL without deleting the secret
remove_ttl(vault_path, "DB_URL")

# Delete all expired secrets (requires passphrase to rewrite vault)
deleted = purge_expired(vault_path, passphrase="my-passphrase")
print(f"Purged: {deleted}")
```

---

## Typical workflow

```
# 1. Store a short-lived deploy token and give it a 1-hour TTL
$ envault set DEPLOY_TOKEN s3cr3t
$ python -c "
from pathlib import Path
from envault.ttl import set_ttl
set_ttl(Path('.envault'), 'DEPLOY_TOKEN', 3600)
"

# 2. Later, in a CI cleanup step, purge anything expired
$ python -c "
from pathlib import Path
from envault.ttl import purge_expired
purged = purge_expired(Path('.envault'), passphrase='$VAULT_PASS')
print('Purged:', purged)
"
```

---

## Error handling

`TTLError` is raised when:

- A TTL value of zero or a negative number is supplied to `set_ttl`.
- The sidecar `.envault_ttl.json` file cannot be read or written.

```python
from envault.ttl import TTLError

try:
    set_ttl(vault_path, "KEY", -1)
except TTLError as e:
    print(f"Bad TTL: {e}")
```

---

## Notes

- TTLs survive `rotate_passphrase` — the sidecar file is independent of
  encryption.
- Snapshots capture the vault contents at a point in time but do **not**
  capture TTL metadata. Restoring a snapshot will not restore expiry times.
- `purge_expired` is idempotent: calling it when nothing has expired is a
  no-op and returns an empty list.
