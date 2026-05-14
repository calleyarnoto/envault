# envault lint

The `lint` command analyses the secrets stored in a vault and reports issues
based on a set of built-in best-practice rules.

## Usage

```bash
envault lint [OPTIONS]
```

### Options

| Option | Default | Description |
|---|---|---|
| `--vault PATH` | `.envault` | Path to the vault file. |
| `--passphrase TEXT` | *(prompted)* | Vault passphrase. |
| `--strict` | off | Exit with status `1` when issues are found. |

## Rules

### `empty_value`

Flags any secret whose value is an empty string or contains only whitespace.
Empty secrets are almost always a configuration mistake.

### `weak_value`

Flags values that match common placeholder patterns such as `password`,
`secret`, `token`, `123…`, `test…`, or `example…`.  These indicate that a
real secret has not yet been supplied.

### `short_value`

Flags non-empty values shorter than **8 characters**.  Very short secrets
provide little entropy and are easier to brute-force.

### `key_naming`

Flags keys that do not follow `UPPER_SNAKE_CASE` convention (e.g. `my_secret`
or `MySecret`).  Consistent naming makes secrets easier to audit and
reference across environments.

## Examples

```bash
# Interactive passphrase prompt
envault lint --vault .envault

# Non-interactive (e.g. CI)
envault lint --vault .envault --passphrase "$VAULT_PASS" --strict
```

### Sample output (issues found)

```
Found 2 issue(s):

  [key_naming] 'db_password' does not follow UPPER_SNAKE_CASE convention.
  [short_value] 'API_KEY' value is shorter than 8 characters.
```

### Sample output (clean)

```
✓ No issues found.
```

## CI Integration

Use `--strict` to fail a pipeline when secrets do not meet quality standards:

```yaml
# GitHub Actions example
- name: Lint vault
  run: envault lint --vault .envault --passphrase "${{ secrets.VAULT_PASS }}" --strict
```
