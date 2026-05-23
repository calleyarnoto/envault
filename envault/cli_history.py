"""CLI commands for per-key secret history."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import click

from envault.cli import _get_vault
from envault.env_history import HistoryError, get_history, record, clear_history


@click.group("history")
def cmd_history():
    """View and manage per-key value history."""


@cmd_history.command("list")
@click.argument("key")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
def history_list(key: str, vault_path: str):
    """List recorded history entries for KEY."""
    p = Path(vault_path)
    try:
        entries = get_history(p, key)
    except HistoryError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not entries:
        click.echo(f"No history recorded for '{key}'.")
        return

    click.echo(f"History for '{key}' ({len(entries)} entries):")
    for i, e in enumerate(entries, 1):
        ts = datetime.fromtimestamp(e.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        note = f"  # {e.note}" if e.note else ""
        click.echo(f"  {i:>3}. [{ts}] {e.value!r}{note}")


@cmd_history.command("clear")
@click.argument("key", required=False, default=None)
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def history_clear(key: str | None, vault_path: str, yes: bool):
    """Clear history for KEY (or all keys if omitted)."""
    p = Path(vault_path)
    target = f"key '{key}'" if key else "ALL keys"
    if not yes:
        click.confirm(f"Clear history for {target}?", abort=True)
    try:
        removed = clear_history(p, key)
    except HistoryError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Cleared {removed} history entries for {target}.")


@cmd_history.command("record")
@click.argument("key")
@click.argument("value")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--note", default="", help="Optional note for this entry.")
def history_record(key: str, value: str, vault_path: str, note: str):
    """Manually record a VALUE for KEY in history."""
    p = Path(vault_path)
    try:
        entry = record(p, key, value, note=note)
    except HistoryError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    ts = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
    click.echo(f"Recorded history entry for '{key}' at {ts}.")
