"""CLI commands for secret reference resolution."""

from __future__ import annotations

import click

from envault.env_secret_ref import RefError, resolve_refs, resolve_all
from envault.cli import _get_vault


@click.group("ref")
def cmd_ref() -> None:
    """Resolve ${KEY} references inside secret values."""


@cmd_ref.command("resolve")
@click.argument("key")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--show-refs", is_flag=True, default=False, help="Print resolved reference keys.")
def resolve_cmd(
    key: str,
    vault_path: str,
    passphrase: str,
    show_refs: bool,
) -> None:
    """Resolve all ${KEY} references in the value of KEY and print the result."""
    try:
        result = resolve_refs(vault_path, passphrase, key)
    except RefError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.resolved)
    if show_refs and result.refs:
        click.echo(f"  refs: {', '.join(result.refs)}", err=True)


@cmd_ref.command("resolve-all")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def resolve_all_cmd(vault_path: str, passphrase: str) -> None:
    """Resolve ${KEY} references for every secret and print a summary."""
    try:
        results = resolve_all(vault_path, passphrase)
    except RefError as exc:
        raise click.ClickException(str(exc)) from exc

    if not results:
        click.echo("Vault is empty.")
        return

    for key, result in sorted(results.items()):
        ref_info = f"  [{', '.join(result.refs)}]" if result.refs else ""
        click.echo(f"{key}={result.resolved}{ref_info}")
