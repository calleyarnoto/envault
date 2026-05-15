"""CLI commands for vault backup and restore."""

from __future__ import annotations

import click
from pathlib import Path

from envault.cli import _get_vault
from envault.env_backup import BackupError, create_backup, list_backups, restore_backup


@click.group("backup")
def cmd_backup() -> None:
    """Backup and restore vault snapshots."""


@cmd_backup.command("create")
@click.option("--vault", "vault_path", default=".envault", show_default=True, help="Vault file path.")
@click.option("--label", default="", help="Optional label embedded in the backup filename.")
@click.option("--no-compress", "compress", is_flag=True, default=True, flag_value=False, help="Skip gzip compression.")
def backup_create(vault_path: str, label: str, compress: bool) -> None:
    """Create a backup of the vault file."""
    try:
        dest = create_backup(Path(vault_path), label=label, compress=compress)
        click.echo(f"Backup created: {dest}")
    except BackupError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_backup.command("list")
@click.option("--vault", "vault_path", default=".envault", show_default=True, help="Vault file path.")
def backup_list(vault_path: str) -> None:
    """List available backups for the vault."""
    backups = list_backups(Path(vault_path))
    if not backups:
        click.echo("No backups found.")
        return
    for path in backups:
        click.echo(str(path))


@cmd_backup.command("restore")
@click.argument("backup_path")
@click.option("--vault", "vault_path", default=".envault", show_default=True, help="Vault file path.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing vault file.")
def backup_restore(backup_path: str, vault_path: str, overwrite: bool) -> None:
    """Restore a vault from BACKUP_PATH."""
    try:
        restore_backup(Path(backup_path), Path(vault_path), overwrite=overwrite)
        click.echo(f"Vault restored from {backup_path} -> {vault_path}")
    except BackupError as exc:
        raise click.ClickException(str(exc)) from exc
