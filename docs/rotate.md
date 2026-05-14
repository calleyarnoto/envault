# Key Rotation

envault supports **passphrase rotation** — re-encrypting all secrets in a vault
under a new passphrase without exposing plaintext values to disk.

## How it works

1. The vault is decrypted in memory using the **current** passphrase.
2. All secret values are re-encrypted using the **new** passphrase.
3. The vault file is overwritten atomically (via the normal `Vault.save()` path).
4. An optional audit log entry is written recording the rotation event.

No plaintext values are written to disk at any point.

## CLI usage

```bash
# Interactive prompts for both passphrases
envault rotate

# Supply passphrases directly (useful in scripts — prefer env vars instead)
envault rotate \
  --old-passphrase "$ENVAULT_OLD_PASS" \
  --new-passphrase "$ENVAULT_NEW_PASS" \
  --new-passphrase-confirmation "$ENVAULT_NEW_PASS"

# With a custom vault path and audit log
envault rotate \
  --vault /path/to/.envault \
  --audit-log /var/log/envault-audit.log
```

## Python API

```python
from pathlib import Path
from envault.rotate import rotate_passphrase
from envault.audit import AuditLog

count = rotate_passphrase(
    vault_path=Path(".envault"),
    old_passphrase="old-secret",
    new_passphrase="new-secret",
    audit_log=AuditLog(Path("audit.log")),
    actor="deploy-script",
)
print(f"{count} secret(s) rotated.")
```

## Error handling

| Situation | Exception raised |
|---|---|
| Vault file not found | `RotationError` |
| Old passphrase is incorrect | `RotationError` |
| New passphrase equals old passphrase | `RotationError` |
| Vault file cannot be written | `RotationError` |

## CI integration

Store the new passphrase as a CI secret **before** running rotation so that
subsequent pipeline steps can still decrypt the vault:

```yaml
# GitHub Actions example
- name: Rotate envault passphrase
  run: |
    envault rotate \
      --old-passphrase "${{ secrets.ENVAULT_OLD_PASS }}" \
      --new-passphrase "${{ secrets.ENVAULT_NEW_PASS }}" \
      --new-passphrase-confirmation "${{ secrets.ENVAULT_NEW_PASS }}"
```
