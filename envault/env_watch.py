"""Watch a vault for secret changes and trigger a callback or shell command."""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from envault.vault import Vault, VaultError


class WatchError(Exception):
    """Raised when vault watching fails."""


@dataclass
class WatchEvent:
    """Describes a change detected between two vault snapshots."""

    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"WatchEvent(added={self.added}, removed={self.removed}, "
            f"changed={self.changed})"
        )


def _snapshot(vault: Vault, passphrase: str) -> dict[str, str]:
    """Return a copy of all secrets in the vault."""
    return {k: vault.get(k, passphrase) for k in vault.list()}


def _diff(old: dict[str, str], new: dict[str, str]) -> WatchEvent:
    old_keys = set(old)
    new_keys = set(new)
    return WatchEvent(
        added=sorted(new_keys - old_keys),
        removed=sorted(old_keys - new_keys),
        changed=sorted(k for k in old_keys & new_keys if old[k] != new[k]),
    )


def watch_vault(
    vault_path: Path,
    passphrase: str,
    *,
    interval: float = 2.0,
    max_iterations: Optional[int] = None,
    on_change: Optional[Callable[[WatchEvent], None]] = None,
    shell_cmd: Optional[str] = None,
) -> None:
    """Poll *vault_path* every *interval* seconds and react to changes.

    Args:
        vault_path: Path to the vault file.
        passphrase: Passphrase used to decrypt secrets.
        interval: Polling interval in seconds.
        max_iterations: Stop after this many iterations (None = run forever).
        on_change: Python callback invoked with a WatchEvent on each change.
        shell_cmd: Shell command executed (via subprocess) when a change occurs.
    """
    if not vault_path.exists():
        raise WatchError(f"Vault not found: {vault_path}")

    vault = Vault(vault_path)
    try:
        prev = _snapshot(vault, passphrase)
    except VaultError as exc:
        raise WatchError(str(exc)) from exc

    iterations = 0
    while max_iterations is None or iterations < max_iterations:
        time.sleep(interval)
        vault = Vault(vault_path)  # reload from disk each cycle
        try:
            curr = _snapshot(vault, passphrase)
        except VaultError:
            iterations += 1
            continue

        event = _diff(prev, curr)
        if event.has_changes:
            if on_change:
                on_change(event)
            if shell_cmd:
                subprocess.run(shell_cmd, shell=True, check=False)  # noqa: S602
            prev = curr
        iterations += 1
