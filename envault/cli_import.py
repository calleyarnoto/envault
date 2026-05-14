"""CLI command: envault import — bulk-import secrets from a .env file."""

from __future__ import annotations

from pathlib import Path

import click

from envault.cli import _get_vault, cli
from envault.import_env import ImportError, import_into_vault


@cli.command("import")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--vault",
    "vault_path",
    default=".envault",
    show_default=True,
    help="Path to the vault file.",
)
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    help="Vault passphrase.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing keys.",
)
def cmd_import(
    env_file: str,
    vault_path: str,
    passphrase: str,
    overwrite: bool,
) -> None:
    """Import secrets from ENV_FILE into the vault.

    Keys that already exist are skipped unless --overwrite is supplied.
    """
    source = Path(env_file).read_text(encoding="utf-8")
    try:
        report = import_into_vault(
            Path(vault_path),
            passphrase,
            source,
            overwrite=overwrite,
        )
    except ImportError as exc:
        raise click.ClickException(str(exc)) from exc

    if not report:
        click.echo("Nothing to import.")
        return

    imported = [(k, s) for k, s in report if s == "imported"]
    overwritten = [(k, s) for k, s in report if s == "overwritten"]
    skipped = [(k, s) for k, s in report if s == "skipped"]

    for key, _ in imported:
        click.echo(f"  imported   {key}")
    for key, _ in overwritten:
        click.echo(f"  overwritten {key}")
    for key, _ in skipped:
        click.echo(f"  skipped    {key} (already exists)")

    click.echo(
        f"\nDone: {len(imported)} imported, "
        f"{len(overwritten)} overwritten, "
        f"{len(skipped)} skipped."
    )
