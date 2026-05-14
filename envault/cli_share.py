"""CLI commands for secret sharing (create-share / import-share)."""

from __future__ import annotations

from pathlib import Path

import click

from envault.cli import _get_vault
from envault.share import ShareError, create_share, import_share


@click.group()
def cmd_share() -> None:
    """Share encrypted secret bundles with other vaults or team members."""


@cmd_share.command("create")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--share-passphrase", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--label", default="", help="Optional label embedded in the bundle.")
@click.option("--out", "out_file", default=None, help="Write bundle to file instead of stdout.")
@click.argument("keys", nargs=-1, required=True)
def create(
    vault_path: str,
    passphrase: str,
    share_passphrase: str,
    label: str,
    out_file: str | None,
    keys: tuple,
) -> None:
    """Create an encrypted share bundle containing the specified KEYS."""
    path = Path(vault_path)
    try:
        bundle = create_share(path, passphrase, list(keys), share_passphrase, label or None)
    except ShareError as exc:
        raise click.ClickException(str(exc))

    if out_file:
        Path(out_file).write_text(bundle)
        click.echo(f"Share bundle written to {out_file} ({len(keys)} key(s)).")
    else:
        click.echo(bundle)


@cmd_share.command("import")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--share-passphrase", prompt=True, hide_input=True)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys.")
@click.argument("bundle_file")
def import_cmd(
    vault_path: str,
    passphrase: str,
    share_passphrase: str,
    overwrite: bool,
    bundle_file: str,
) -> None:
    """Import secrets from a BUNDLE_FILE into the vault."""
    bundle = Path(bundle_file).read_text().strip()
    path = Path(vault_path)
    try:
        count = import_share(bundle, share_passphrase, path, passphrase, overwrite=overwrite)
    except ShareError as exc:
        raise click.ClickException(str(exc))

    click.echo(f"Imported {count} secret(s) into {vault_path}.")
