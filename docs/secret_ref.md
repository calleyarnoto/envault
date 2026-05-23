# Secret References

envault supports **secret references** — values that embed `${KEY}` placeholders
which are resolved at read-time by substituting the value of the referenced key.

## Syntax

Any secret value may contain one or more references using the `${KEY}` syntax:

```
HOST=db.internal
DSN=postgres://${HOST}/myapp
```

When you resolve `DSN`, envault replaces `${HOST}` with `db.internal`, producing:

```
postgres://db.internal/myapp
```

## CLI Usage

### Resolve a single key

```bash
envault ref resolve DSN --vault .envault
```

Add `--show-refs` to see which keys were substituted:

```bash
envault ref resolve DSN --show-refs
```

### Resolve all keys

```bash
envault ref resolve-all --vault .envault
```

Output lists every key with its fully-resolved value. Keys that participated in
a substitution are annotated with the referenced key names.

## Python API

```python
from envault.env_secret_ref import resolve_refs, resolve_all

# Single key
result = resolve_refs(".envault", passphrase, "DSN")
print(result.resolved)  # postgres://db.internal/myapp
print(result.refs)      # ['HOST']

# All keys
results = resolve_all(".envault", passphrase)
for key, r in results.items():
    print(f"{key} = {r.resolved}")
```

## Chained References

References can be chained — a value may reference a key whose value itself
contains references. The default maximum depth is **10** to prevent runaway
resolution.

## Error Handling

| Situation | Exception |
|---|---|
| Key not found in vault | `RefError` |
| Referenced key not found | `RefError` |
| Circular reference detected | `RefError` |
| Max depth exceeded | `RefError` |

## Limitations

- Only `${KEY}` syntax is supported (`$KEY` without braces is ignored).
- References are resolved at read-time; the raw value with placeholders is what
  is stored and encrypted in the vault.
