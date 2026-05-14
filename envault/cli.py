"""Command-line interface for envault vault operations."""

import sys
from pathlib import Path

import click

from envault.vault import Vault, VaultError, init_vault, DEFAULT_VAULT_FILENAME


def _get_vault(vault_file: str, passphrase: str) -> Vault:
    v = Vault(Path(vault_file), passphrase)
    v.load()
    return v


@click.group()
def cli() -> None:
    """envault — secure .env file manager."""


@cli.command("init")
@click.option("--vault", default=DEFAULT_VAULT_FILENAME, show_default=True, help="Vault file path.")
@click.password_option("--passphrase", prompt="Passphrase", help="Encryption passphrase.")
def cmd_init(vault: str, passphrase: str) -> None:
    """Initialise a new empty vault."""
    try:
        init_vault(Path(vault), passphrase)
        click.echo(f"Vault initialised at {vault}")
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--vault", default=DEFAULT_VAULT_FILENAME, show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def cmd_set(key: str, value: str, vault: str, passphrase: str) -> None:
    """Add or update a secret in the vault."""
    try:
        v = _get_vault(vault, passphrase)
        v.set(key, value)
        v.save()
        click.echo(f"Secret '{key}' saved.")
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command("get")
@click.argument("key")
@click.option("--vault", default=DEFAULT_VAULT_FILENAME, show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def cmd_get(key: str, vault: str, passphrase: str) -> None:
    """Print the value of a secret."""
    try:
        v = _get_vault(vault, passphrase)
        value = v.get(key)
        if value is None:
            click.echo(f"Key '{key}' not found.", err=True)
            sys.exit(1)
        click.echo(value)
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command("list")
@click.option("--vault", default=DEFAULT_VAULT_FILENAME, show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def cmd_list(vault: str, passphrase: str) -> None:
    """List all secret keys stored in the vault."""
    try:
        v = _get_vault(vault, passphrase)
        keys = v.list_keys()
        if not keys:
            click.echo("Vault is empty.")
        else:
            click.echo("\n".join(keys))
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command("export")
@click.option("--vault", default=DEFAULT_VAULT_FILENAME, show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def cmd_export(vault: str, passphrase: str) -> None:
    """Print secrets as shell export statements."""
    try:
        v = _get_vault(vault, passphrase)
        click.echo(v.export_env())
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
