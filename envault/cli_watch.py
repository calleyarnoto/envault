"""CLI command: envault watch — poll a vault and react to secret changes."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.env_watch import WatchError, WatchEvent, watch_vault


@click.group("watch")
def cmd_watch() -> None:
    """Watch a vault for secret changes."""


@cmd_watch.command("start")
@click.option(
    "--vault",
    "vault_path",
    default=".envault",
    show_default=True,
    help="Path to vault file.",
)
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    help="Vault passphrase.",
)
@click.option(
    "--interval",
    default=2.0,
    show_default=True,
    type=float,
    help="Polling interval in seconds.",
)
@click.option(
    "--exec",
    "shell_cmd",
    default=None,
    help="Shell command to run when changes are detected.",
)
def start(
    vault_path: str,
    passphrase: str,
    interval: float,
    shell_cmd: str | None,
) -> None:
    """Start watching the vault for changes."""
    path = Path(vault_path)

    def _on_change(event: WatchEvent) -> None:
        if event.added:
            click.echo(f"  [+] added:   {', '.join(event.added)}")
        if event.removed:
            click.echo(f"  [-] removed: {', '.join(event.removed)}")
        if event.changed:
            click.echo(f"  [~] changed: {', '.join(event.changed)}")
        click.echo("")

    click.echo(f"Watching {path} (interval={interval}s) — press Ctrl+C to stop.")
    try:
        watch_vault(
            path,
            passphrase,
            interval=interval,
            on_change=_on_change,
            shell_cmd=shell_cmd,
        )
    except WatchError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("Stopped.")
