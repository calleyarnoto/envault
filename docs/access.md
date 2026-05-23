# Access Control

envault supports a lightweight role-based access control (RBAC) layer that lets
you declare which roles (e.g. `ci`, `developer`, `admin`) may **read** or
**write** specific secrets within a vault.

Access rules are stored in a plain JSON sidecar file (`.envault_access.json`)
next to the vault file.  The file is human-readable and can be committed to
version control alongside the encrypted vault.

---

## Concepts

| Term | Meaning |
|---|---|
| **role** | An arbitrary string identifier such as `ci`, `admin`, or a GitHub username. |
| **permission** | Either `read` or `write`. |
| **key** | The name of a secret stored in the vault. |

Granting `write` permission does **not** automatically grant `read`; the two
permissions are tracked independently.

---

## Python API

```python
from envault.env_access import grant_access, revoke_access, list_access, can_access
from pathlib import Path

vault = Path("myproject.vault")

# Grant the CI role read access to two keys
grant_access(vault, role="ci", keys=["DB_HOST", "API_KEY"])

# Grant admin write access
grant_access(vault, role="admin", keys=["DB_PASS"], permission="write")

# Check access
if can_access(vault, role="ci", key="API_KEY"):
    print("ci may read API_KEY")

# List all rules
print(list_access(vault))
# {'ci': {'read': ['DB_HOST', 'API_KEY'], 'write': []},
#  'admin': {'read': [], 'write': ['DB_PASS']}}

# Revoke a key
revoke_access(vault, role="ci", keys=["DB_HOST"])
```

---

## Errors

`AccessError` is raised when:

- The vault file does not exist.
- The role string is empty or whitespace.
- An unknown permission string (not `read` or `write`) is supplied.
- No keys are provided to `grant_access`.

---

## Access-map file format

```json
{
  "ci": {
    "read": ["DB_HOST", "API_KEY"],
    "write": []
  },
  "admin": {
    "read": [],
    "write": ["DB_PASS"]
  }
}
```

The file is written atomically on every `grant_access` or `revoke_access` call.

---

## Notes

- envault does **not** enforce access rules at the crypto layer; enforcement is
  the responsibility of the calling application or CI pipeline.
- The access map is intentionally kept separate from the encrypted vault so it
  can be inspected without a passphrase.
