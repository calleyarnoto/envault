# Vault Event Notifications

`envault` can fire a webhook whenever a secret is modified, rotated, imported, or deleted. This lets you integrate with Slack, PagerDuty, custom audit services, or any HTTP endpoint.

## Quick start

```bash
# Register a webhook for a vault
envault notify set-webhook my.vault https://hooks.example.com/envault

# Confirm the URL is saved
envault notify show my.vault

# Send a test payload
envault notify test my.vault

# Remove the webhook
envault notify clear my.vault
```

## Webhook payload

Every notification is a JSON `POST` request:

```json
{
  "vault": "/path/to/my.vault",
  "action": "set",
  "keys": ["DATABASE_URL"],
  "timestamp": 1718000000.123
}
```

| Field | Type | Description |
|-------|------|-------------|
| `vault` | string | Absolute path to the vault file |
| `action` | string | Event type: `set`, `delete`, `rotate`, `import`, `test` |
| `keys` | array | Secret keys affected by the action |
| `timestamp` | float | Unix epoch time of the event |

## Python API

```python
from envault.env_notify import NotifyEvent, fire, set_webhook

# Configure once
set_webhook("/path/to/my.vault", "https://hooks.example.com/envault")

# Fire after mutating secrets
event = NotifyEvent(
    vault_path="/path/to/my.vault",
    action="set",
    keys=["API_KEY", "DB_PASS"],
)
fire(event)  # Returns True if webhook was called, False if none configured
```

## Error handling

`fire()` raises `NotifyError` if the webhook returns HTTP 4xx/5xx or if the connection fails. The CLI surfaces this as a non-zero exit code.

If no webhook is configured, `fire()` returns `False` silently — existing workflows are unaffected.

## Security considerations

- Webhook URLs are stored in a sidecar file (`<vault>.notify.json`) **next to the vault**. Ensure this file has appropriate filesystem permissions.
- Payloads contain **key names only** — secret values are never transmitted.
- Use HTTPS endpoints to protect the payload in transit.
