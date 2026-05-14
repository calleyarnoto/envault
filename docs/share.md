# Secret Sharing

`envault` lets you securely share a subset of secrets with a colleague or
another vault without exposing your vault passphrase.  The share bundle is
encrypted with a *separate* share passphrase, so you can transmit it safely
over email, Slack, or a CI secret store.

---

## Creating a share bundle

```bash
envault share create TOKEN API_KEY \
  --vault .envault \
  --out bundle.enc
```

You will be prompted for:
1. **Vault passphrase** – to open your vault.
2. **Share passphrase** – a new passphrase used to encrypt the bundle
   (confirm prompt included).

Omit `--out` to print the encrypted bundle directly to stdout.

### Optional label

```bash
envault share create TOKEN --label "staging-deploy" --out bundle.enc
```

The label is stored inside the encrypted bundle and is visible only after
decryption.

---

## Importing a share bundle

The recipient runs:

```bash
envault share import bundle.enc --vault .envault
```

They will be prompted for:
1. **Vault passphrase** – to open *their* vault.
2. **Share passphrase** – provided by the sender out-of-band.

### Overwriting existing keys

By default, importing a bundle that contains a key already present in the
target vault raises an error.  Use `--overwrite` to allow replacement:

```bash
envault share import bundle.enc --vault .envault --overwrite
```

---

## Python API

```python
from pathlib import Path
from envault.share import create_share, read_share, import_share

# Create
bundle = create_share(
    vault_path=Path(".envault"),
    passphrase="vault-pass",
    keys=["TOKEN", "API_KEY"],
    share_passphrase="share-pass",
    label="handoff-2024",
)

# Inspect without importing
secrets = read_share(bundle, "share-pass")
print(secrets)  # {'TOKEN': '...', 'API_KEY': '...'}

# Import into another vault
count = import_share(
    bundle=bundle,
    share_passphrase="share-pass",
    vault_path=Path("other/.envault"),
    passphrase="other-vault-pass",
    overwrite=False,
)
print(f"Imported {count} secret(s).")
```

---

## Security notes

* The bundle is encrypted with the same AES-256-GCM + Argon2 key-derivation
  used by the vault itself (see `envault/crypto.py`).
* Your **vault passphrase is never included** in the bundle.
* Transmit the share passphrase via a separate, secure channel (e.g.
  1Password, Signal).
* Bundles have no expiry — delete them after the recipient has imported the
  secrets.
