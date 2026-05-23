"""Notification hooks for vault events (webhook, stdout, file log)."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    import urllib.request as _urllib
except ImportError:  # pragma: no cover
    _urllib = None  # type: ignore


class NotifyError(Exception):
    """Raised when a notification cannot be delivered."""


@dataclass
class NotifyEvent:
    vault_path: str
    action: str          # e.g. "set", "delete", "rotate", "import"
    keys: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "vault": self.vault_path,
            "action": self.action,
            "keys": self.keys,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        return (
            f"NotifyEvent(action={self.action!r}, keys={self.keys!r}, "
            f"vault={self.vault_path!r})"
        )


def _notify_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".notify.json")


def _load_config(vault_path: str) -> dict:
    p = _notify_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_config(vault_path: str, config: dict) -> None:
    _notify_path(vault_path).write_text(json.dumps(config, indent=2))


def set_webhook(vault_path: str, url: str) -> None:
    """Persist a webhook URL for the given vault."""
    if not vault_path or not Path(vault_path).exists():
        raise NotifyError(f"Vault not found: {vault_path}")
    if not url.startswith(("http://", "https://")):
        raise NotifyError(f"Invalid webhook URL: {url!r}")
    config = _load_config(vault_path)
    config["webhook"] = url
    _save_config(vault_path, config)


def get_webhook(vault_path: str) -> Optional[str]:
    """Return the configured webhook URL, or None."""
    return _load_config(vault_path).get("webhook")


def clear_webhook(vault_path: str) -> None:
    """Remove the webhook URL from the notify config."""
    config = _load_config(vault_path)
    config.pop("webhook", None)
    _save_config(vault_path, config)


def fire(event: NotifyEvent, *, timeout: int = 5) -> bool:
    """
    Deliver *event* to the configured webhook (if any).
    Returns True if a webhook was called, False if none is configured.
    Raises NotifyError on delivery failure.
    """
    url = get_webhook(event.vault_path)
    if not url:
        return False
    payload = json.dumps(event.to_dict()).encode()
    req = _urllib.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _urllib.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            if resp.status >= 400:
                raise NotifyError(
                    f"Webhook returned HTTP {resp.status} for {url!r}"
                )
    except Exception as exc:
        if isinstance(exc, NotifyError):
            raise
        raise NotifyError(f"Webhook delivery failed: {exc}") from exc
    return True
