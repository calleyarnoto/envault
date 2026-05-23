# Schema Validation

envault supports defining a schema for your vault secrets to enforce types, patterns, and required keys. This helps catch misconfigured environments before deployment.

## Schema File

Schemas are stored alongside the vault file as `<vault-name>.schema.json`. The file is created automatically when you define the first rule.

## Supported Rules

| Rule | Description | Example value |
|------|-------------|---------------|
| `type` | Enforce a value type | `integer`, `boolean`, `url`, `email`, `string` |
| `pattern` | Regex the value must match | `^\d{4}$` |
| `required` | Key must be present in vault | `true` |
| `min_length` | Minimum character length | `8` |
| `max_length` | Maximum character length | `128` |

## Supported Types

- **string** — any value (no format check)
- **integer** — matches `-?\d+`
- **boolean** — `true`, `false`, `1`, `0`, `yes`, `no` (case-insensitive)
- **url** — must start with `http://` or `https://`
- **email** — basic `user@domain.tld` format

## Python API

```python
from envault.env_schema import set_schema_rule, validate_vault, get_schema

vault_path = Path(".envault/project.vault")

# Define rules
set_schema_rule(vault_path, "PORT", "type", "integer")
set_schema_rule(vault_path, "PORT", "required", "true")
set_schema_rule(vault_path, "API_KEY", "min_length", "16")
set_schema_rule(vault_path, "WEBHOOK_URL", "type", "url")

# Inspect schema
schema = get_schema(vault_path)
print(schema)
# {'PORT': {'type': 'integer', 'required': 'true'}, ...}

# Run validation
violations = validate_vault(vault_path, passphrase="my-secret")
for v in violations:
    print(f"[{v.rule}] {v.key}: {v.message}")
```

## Errors

- `SchemaError` — raised when the vault is missing, a rule name is unknown, or a type name is invalid.
- `SchemaViolation` — a dataclass describing a single validation failure with `key`, `rule`, and `message` fields.

## Notes

- The schema file is **not encrypted** — avoid storing sensitive information in rule values (e.g., don't put real secrets in `pattern`).
- Keys present in the vault but not in the schema are silently ignored.
- Keys in the schema marked `required` but absent from the vault always produce a violation, regardless of other rules.
