# Secret Policy Enforcement

envault lets you define per-project **policies** that are checked against your vault's secrets. Policies help enforce naming conventions and value constraints across your team.

## Policy Rules

| Rule | Description | Example value |
|---|---|---|
| `key_pattern` | Regex that every key must fully match | `[A-Z][A-Z0-9_]+` |
| `min_length` | Minimum character length for values | `8` |
| `max_length` | Maximum character length for values | `128` |
| `required_prefix` | Every key must start with this string | `APP_` |
| `forbidden_prefix` | No key may start with this string | `DEBUG_` |

Policy rules are stored in a sidecar file next to your vault:
```
myproject.vault
myproject.policy.json   ← auto-managed by envault
```

## CLI Usage

### Set a rule

```bash
envault policy set --vault myproject.vault key_pattern "[A-Z_]+"
envault policy set --vault myproject.vault min_length 8
envault policy set --vault myproject.vault required_prefix APP_
```

### View current policy

```bash
envault policy show --vault myproject.vault
```

Example output:
```
key_pattern   : [A-Z_]+
min_length    : 8
required_prefix: APP_
```

### Check vault against policy

```bash
envault policy check --vault myproject.vault
```

Example output when violations exist:
```
[key_pattern]  DEBUG does not match pattern [A-Z_]+
[min_length]   APP_TOKEN value is shorter than minimum length 8
2 violation(s) found.
```

Exits with code `0` when there are no violations, `1` when violations are found.

## Python API

```python
from pathlib import Path
from envault.env_policy import set_policy, get_policy, check_policy

vault_path = Path("myproject.vault")

# Define rules
set_policy(vault_path, "key_pattern", "[A-Z_]+")
set_policy(vault_path, "min_length", "8")

# Inspect rules
policy = get_policy(vault_path)
print(policy)  # {'key_pattern': '[A-Z_]+', 'min_length': '8'}

# Validate
violations = check_policy(vault_path, passphrase="my-secret-pass")
for v in violations:
    print(f"[{v.rule}] {v.message}")
```

## CI Integration

Add a policy check step to your pipeline to catch violations before deployment:

```yaml
# GitHub Actions example
- name: Check envault policy
  run: envault policy check --vault ${{ secrets.VAULT_PATH }}
  env:
    ENVAULT_PASSPHRASE: ${{ secrets.VAULT_PASS }}
```

## Notes

- The policy file is **not encrypted** — it contains only structural rules, never secret values.
- It is safe (and recommended) to commit the `.policy.json` file to version control.
- Rules are additive; all defined rules are checked independently.
