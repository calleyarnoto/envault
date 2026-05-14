# Secret Tags

envault supports tagging secrets so you can group and filter them by logical
category (e.g. `database`, `external`, `production`).

## Concepts

* A **tag** is a plain string label attached to one or more secret keys.
* Tags are stored inside the vault itself (encrypted alongside your secrets),
  so they travel with the vault file and are never stored in plain text.
* A single secret key can carry multiple tags; a single tag can apply to
  multiple keys.

## Python API

```python
from envault.vault import Vault
from envault.tags import add_tag, remove_tag, list_tags, keys_for_tag, all_tags

vault = Vault("my-project/.envault")
passphrase = "correct-horse-battery-staple"

# Tag a secret
add_tag(vault, "DB_URL", "database", passphrase)
add_tag(vault, "DB_URL", "production", passphrase)
add_tag(vault, "CACHE_URL", "database", passphrase)

# List tags on a key
print(list_tags(vault, "DB_URL"))   # ['database', 'production']

# Find all keys with a given tag
print(keys_for_tag(vault, "database"))  # ['DB_URL', 'CACHE_URL']

# Remove a tag
remove_tag(vault, "DB_URL", "production", passphrase)

# Full tag map
print(all_tags(vault))
# {'DB_URL': ['database'], 'CACHE_URL': ['database']}
```

## Storage Details

Tags are serialised as a JSON object and stored under the reserved key
`__tags__` inside the encrypted vault.  This key is excluded from normal
`list` / `export` operations so it does not pollute your environment.

## Error Handling

| Exception | Cause |
|-----------|-------|
| `TagError` | Attempting to add an empty string as a tag. |

## Notes

* Tag names are case-sensitive (`database` ≠ `Database`).
* `add_tag` is idempotent — calling it twice with the same key/tag pair has
  no effect.
* `remove_tag` returns `True` if the tag was removed and `False` if it was
  not present, making it safe to call unconditionally.
