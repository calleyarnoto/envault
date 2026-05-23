"""CLI commands for vault quota management."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_quota import (
    QuotaError,
    set_quota,
    get_quota,
    check_quota,
    clear_quota,
)


@click.group("quota")
def cmd_quota():
    """Manage per-vault secret quotas."""


@cmd_quota.command("set")
@click.argument("vault")
@click.argument("max_secrets", type=int)
def quota_set(vault: str, max_secrets: int):
    """Set the maximum number of secrets for VAULT."""
    vault_path = Path(vault)
    try:
        result = set_quota(vault_path, max_secrets)
        click.echo(f"Quota set: {result} secrets maximum.")
    except QuotaError as exc:
        raise click.ClickException(str(exc))


@cmd_quota.command("show")
@click.argument("vault")
@click.option("--passphrase", "-p", envvar="ENVAULT_PASSPHRASE", default="", show_default=False)
def quota_show(vault: str, passphrase: str):
    """Show quota status for VAULT."""
    vault_path = Path(vault)
    limit = get_quota(vault_path)
    if limit is None:
        click.echo("No quota configured.")
        return
    if not passphrase:
        click.echo(f"Quota limit: {limit} secrets (use --passphrase to see current usage).")
        return
    try:
        status = check_quota(vault_path, passphrase)
        click.echo(
            f"Secrets: {status['current']}/{status['limit']}  "
            f"({'AT LIMIT' if status['at_limit'] else 'OK'})"
        )
    except QuotaError as exc:
        raise click.ClickException(str(exc))


@cmd_quota.command("clear")
@click.argument("vault")
def quota_clear(vault: str):
    """Remove the quota setting for VAULT."""
    clear_quota(Path(vault))
    click.echo("Quota cleared.")
