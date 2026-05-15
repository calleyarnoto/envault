"""CLI commands for secret aliasing."""
from __future__ import annotations

import click
from pathlib import Path

from envault.cli import _get_vault
from envault.env_alias import (
    AliasError,
    add_alias,
    remove_alias,
    resolve_alias,
    list_aliases,
)


@click.group("alias")
def cmd_alias():
    """Manage secret aliases."""


@cmd_alias.command("add")
@click.argument("alias_name")
@click.argument("target_key")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
def alias_add(alias_name: str, target_key: str, vault_path: str, passphrase: str):
    """Add ALIAS_NAME as an alias for TARGET_KEY."""
    vp = Path(vault_path)
    try:
        value = add_alias(vp, alias_name, target_key, passphrase)
        click.echo(f"Alias '{alias_name}' -> '{target_key}' created. Value: {value}")
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_alias.command("remove")
@click.argument("alias_name")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
def alias_remove(alias_name: str, vault_path: str):
    """Remove an existing alias."""
    vp = Path(vault_path)
    try:
        remove_alias(vp, alias_name)
        click.echo(f"Alias '{alias_name}' removed.")
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_alias.command("resolve")
@click.argument("alias_name")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
def alias_resolve(alias_name: str, vault_path: str, passphrase: str):
    """Print the value that ALIAS_NAME resolves to."""
    vp = Path(vault_path)
    try:
        value = resolve_alias(vp, alias_name, passphrase)
        click.echo(value)
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_alias.command("list")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
def alias_list(vault_path: str):
    """List all defined aliases."""
    vp = Path(vault_path)
    entries = list_aliases(vp)
    if not entries:
        click.echo("No aliases defined.")
        return
    for entry in entries:
        click.echo(f"  {entry['alias']:30s} -> {entry['target']}")
