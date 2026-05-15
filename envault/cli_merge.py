"""CLI sub-command: merge secrets from one vault into another."""

from __future__ import annotations

import click

from envault.env_merge import MergeError, merge_vaults


@click.group("merge")
def cmd_merge() -> None:
    """Merge secrets from a source vault into a destination vault."""


@cmd_merge.command("run")
@click.argument("src", metavar="SRC_VAULT")
@click.argument("dst", metavar="DST_VAULT")
@click.option(
    "--src-pass",
    prompt="Source passphrase",
    hide_input=True,
    help="Passphrase for the source vault.",
)
@click.option(
    "--dst-pass",
    prompt="Destination passphrase",
    hide_input=True,
    help="Passphrase for the destination vault.",
)
@click.option(
    "--key",
    "keys",
    multiple=True,
    metavar="KEY",
    help="Specific key(s) to merge (repeatable). Merges all when omitted.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing keys in the destination vault.",
)
def run(
    src: str,
    dst: str,
    src_pass: str,
    dst_pass: str,
    keys: tuple,
    overwrite: bool,
) -> None:
    """Merge secrets from SRC_VAULT into DST_VAULT."""
    try:
        result = merge_vaults(
            src,
            src_pass,
            dst,
            dst_pass,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
        )
    except MergeError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Merge complete: {result.summary()}")
    if result.added:
        for k in sorted(result.added):
            click.echo(f"  + {k}")
    if result.overwritten:
        for k in sorted(result.overwritten):
            click.echo(f"  ~ {k} (overwritten)")
    if result.skipped:
        for k in sorted(result.skipped):
            click.echo(f"  - {k} (skipped)")
