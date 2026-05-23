"""CLI commands for envault group management."""
from __future__ import annotations

import click

from envault.cli import _get_vault
from envault.env_group import GroupError, create_group, delete_group, list_groups, get_group_secrets


@click.group("group")
def cmd_group() -> None:
    """Manage named groups of secrets."""


@cmd_group.command("create")
@click.argument("group")
@click.argument("keys", nargs=-1, required=True)
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.password_option("--passphrase", prompt="Passphrase", confirmation_prompt=False)
def group_create(group: str, keys: tuple, vault_path: str, passphrase: str) -> None:
    """Create or update GROUP with the given KEYS."""
    vp = _get_vault(vault_path)
    try:
        count = create_group(vp, group, list(keys), passphrase)
        click.echo(f"Group '{group}' saved with {count} key(s).")
    except GroupError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_group.command("delete")
@click.argument("group")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
def group_delete(group: str, vault_path: str) -> None:
    """Delete GROUP (secrets are kept in the vault)."""
    vp = _get_vault(vault_path)
    try:
        delete_group(vp, group)
        click.echo(f"Group '{group}' deleted.")
    except GroupError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_group.command("list")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
def group_list(vault_path: str) -> None:
    """List all groups and their keys."""
    vp = _get_vault(vault_path)
    groups = list_groups(vp)
    if not groups:
        click.echo("No groups defined.")
        return
    for name, keys in sorted(groups.items()):
        click.echo(f"{name}: {', '.join(keys)}")


@cmd_group.command("show")
@click.argument("group")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.password_option("--passphrase", prompt="Passphrase", confirmation_prompt=False)
def group_show(group: str, vault_path: str, passphrase: str) -> None:
    """Show decrypted key=value pairs for GROUP."""
    vp = _get_vault(vault_path)
    try:
        secrets = get_group_secrets(vp, group, passphrase)
        for k, v in sorted(secrets.items()):
            click.echo(f"{k}={v}")
    except GroupError as exc:
        raise click.ClickException(str(exc)) from exc
