"""Profile support — manage named environment profiles (e.g. dev, staging, prod)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault, VaultError

PROFILE_FILE = ".envault_profiles.json"


class ProfileError(Exception):
    """Raised when a profile operation fails."""


def _profile_path(vault_path: Path) -> Path:
    return vault_path.parent / PROFILE_FILE


def _load_profiles(vault_path: Path) -> Dict[str, List[str]]:
    """Return mapping of profile_name -> list of secret keys."""
    p = _profile_path(vault_path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise ProfileError(f"Failed to read profile file: {exc}") from exc


def _save_profiles(vault_path: Path, profiles: Dict[str, List[str]]) -> None:
    p = _profile_path(vault_path)
    try:
        p.write_text(json.dumps(profiles, indent=2, sort_keys=True))
    except OSError as exc:
        raise ProfileError(f"Failed to write profile file: {exc}") from exc


def create_profile(vault_path: Path, profile: str, keys: List[str], passphrase: str) -> int:
    """Associate *keys* with *profile*.  Returns number of keys registered."""
    if not profile.strip():
        raise ProfileError("Profile name must not be empty.")
    if not keys:
        raise ProfileError("At least one key must be provided.")

    vault = Vault(vault_path)
    vault.load(passphrase)
    missing = [k for k in keys if k not in vault.list()]
    if missing:
        raise ProfileError(f"Keys not found in vault: {', '.join(missing)}")

    profiles = _load_profiles(vault_path)
    profiles[profile] = sorted(set(keys))
    _save_profiles(vault_path, profiles)
    return len(profiles[profile])


def list_profiles(vault_path: Path) -> List[str]:
    """Return sorted list of profile names."""
    return sorted(_load_profiles(vault_path).keys())


def get_profile_keys(vault_path: Path, profile: str) -> List[str]:
    """Return the keys registered under *profile*."""
    profiles = _load_profiles(vault_path)
    if profile not in profiles:
        raise ProfileError(f"Profile '{profile}' does not exist.")
    return profiles[profile]


def delete_profile(vault_path: Path, profile: str) -> None:
    """Remove *profile* from the profile map."""
    profiles = _load_profiles(vault_path)
    if profile not in profiles:
        raise ProfileError(f"Profile '{profile}' does not exist.")
    del profiles[profile]
    _save_profiles(vault_path, profiles)


def export_profile(vault_path: Path, profile: str, passphrase: str) -> Dict[str, str]:
    """Return a dict of {key: secret_value} for all keys in *profile*."""
    keys = get_profile_keys(vault_path, profile)
    vault = Vault(vault_path)
    vault.load(passphrase)
    return {k: vault.get(k, passphrase) for k in keys}
