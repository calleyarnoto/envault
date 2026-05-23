# Vault Quota Management

Envault supports per-vault **secret quotas** — a hard limit on how many secrets
a vault may contain. This is useful in shared or CI environments where you want
to keep configuration lean and prevent accidental sprawl.

## Commands

### Set a quota

```bash
envault quota set <vault> <max_secrets>
```

Sets the maximum number of secrets allowed in the vault.

```bash
envault quota set project.vault 50
# Quota set: 50 secrets maximum.
```

### Show quota status

```bash
envault quota show <vault> [--passphrase <pass>]
```

Without `--passphrase`, shows only the configured limit:

```bash
envault quota show project.vault
# Quota limit: 50 secrets (use --passphrase to see current usage).
```

With `--passphrase`, shows current usage vs. the limit:

```bash
envault quota show project.vault --passphrase mysecret
# Secrets: 12/50  (OK)
```

When the vault is at capacity:

```bash
# Secrets: 50/50  (AT LIMIT)
```

### Clear quota

```bash
envault quota clear <vault>
```

Removes the quota restriction entirely.

```bash
envault quota clear project.vault
# Quota cleared.
```

## Python API

```python
from pathlib import Path
from envault.env_quota import set_quota, get_quota, check_quota, enforce_quota, clear_quota

vault = Path("project.vault")

# Configure a quota
set_quota(vault, 25)

# Read the configured limit
print(get_quota(vault))  # 25

# Check current usage
status = check_quota(vault, "passphrase")
# {'current': 3, 'limit': 25, 'at_limit': False}

# Raise QuotaError if at limit (useful before vault.set())
enforce_quota(vault, "passphrase")

# Remove the quota
clear_quota(vault)
```

## Quota file

Quota settings are stored alongside the vault in a `<name>.quota.json` file.
This file is safe to commit to version control — it contains no secrets.

## Notes

- The quota is **not** enforced automatically by `vault.set()`; call
  `enforce_quota()` in your workflow before adding new secrets.
- Setting a quota lower than the current secret count does **not** delete
  secrets; it simply means `enforce_quota()` will immediately raise.
- The `ENVAULT_PASSPHRASE` environment variable is respected by
  `quota show` when `--passphrase` is not supplied on the command line.
