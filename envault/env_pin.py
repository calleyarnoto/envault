"""envault.env_pin — Pin secrets to a specific version/value and prevent accidental overwrites."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class PinError(Exception):
    """Raised when a pin operation fails."""


def _pin_path(vault_path: Path) -> Path:
    return vault_path.parent / (vault_path.stem + ".pins.json")


def _load_pins(vault_path: Path) -> Dict[str, str]:
    p = _pin_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_pins(vault_path: Path, pins: Dict[str, str]) -> None:
    _pin_path(vault_path).write_text(json.dumps(pins, indent=2))


def pin_secret(vault_path: Path, passphrase: str, key: str) -> str:
    """Pin *key* to its current value. Returns the pinned value."""
    if not vault_path.exists():
        raise PinError(f"Vault not found: {vault_path}")
    v = Vault(vault_path, passphrase)
    secrets = v.all()
    if key not in secrets:
        raise PinError(f"Key '{key}' not found in vault.")
    pins = _load_pins(vault_path)
    pins[key] = secrets[key]
    _save_pins(vault_path, pins)
    return secrets[key]


def unpin_secret(vault_path: Path, key: str) -> None:
    """Remove the pin for *key*. Raises PinError if key is not pinned."""
    pins = _load_pins(vault_path)
    if key not in pins:
        raise PinError(f"Key '{key}' is not pinned.")
    del pins[key]
    _save_pins(vault_path, pins)


def list_pins(vault_path: Path) -> List[str]:
    """Return sorted list of pinned key names."""
    return sorted(_load_pins(vault_path).keys())


def check_pins(vault_path: Path, passphrase: str) -> Dict[str, bool]:
    """Check each pinned key against the current vault value.

    Returns a dict mapping key -> True (matches pin) or False (drifted).
    """
    if not vault_path.exists():
        raise PinError(f"Vault not found: {vault_path}")
    pins = _load_pins(vault_path)
    if not pins:
        return {}
    v = Vault(vault_path, passphrase)
    secrets = v.all()
    return {key: secrets.get(key) == pinned_val for key, pinned_val in pins.items()}
