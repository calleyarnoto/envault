# Secret Expiry

envault lets you attach an **expiry date** to any secret. Once a secret has
passed its expiry timestamp it can be listed and automatically purged from the
vault.

## Setting an expiry

```python
from envault.env_expire import set_expiry

# Expire API_KEY in 30 days
ts = set_expiry(vault_path, "API_KEY", days=30, passphrase="my-pass")
print(f"Expires at UNIX timestamp: {ts}")
```

## Checking an expiry

```python
from envault.env_expire import get_expiry
import datetime

ts = get_expiry(vault_path, "API_KEY")
if ts:
    dt = datetime.datetime.utcfromtimestamp(ts)
    print(f"API_KEY expires {dt} UTC")
else:
    print("No expiry set")
```

## Listing expired secrets

```python
from envault.env_expire import list_expired

for key, ts in list_expired(vault_path, passphrase="my-pass"):
    print(f"{key} expired at {ts}")
```

## Purging expired secrets

```python
from envault.env_expire import purge_expired

purged = purge_expired(vault_path, passphrase="my-pass")
print(f"Removed {len(purged)} expired secret(s): {purged}")
```

## Error handling

`ExpireError` is raised when:

- `days` is zero or negative.
- The target key does not exist in the vault.

```python
from envault.env_expire import ExpireError

try:
    set_expiry(vault_path, "MISSING_KEY", days=7, passphrase="my-pass")
except ExpireError as exc:
    print(f"Error: {exc}")
```

## Storage

Expiry metadata is stored alongside the vault file with the suffix
`.expire.json`.  This file is **not** encrypted — only the timestamps are
stored, never the secret values.  Add `*.expire.json` to your `.gitignore` if
you do not want expiry metadata committed.
