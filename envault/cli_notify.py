"""CLI sub-commands for managing vault event notifications."""
from __future__ import annotations

import click

from envault.env_notify import NotifyError, NotifyEvent, clear_webhook, fire, get_webhook, set_webhook


@click.group("notify")
def cmd_notify() -> None:
    """Manage webhook notifications for vault events."""


@cmd_notify.command("set-webhook")
@click.argument("vault")
@click.argument("url")
def notify_set_webhook(vault: str, url: str) -> None:
    """Register a webhook URL for VAULT events."""
    try:
        set_webhook(vault, url)
        click.echo(f"Webhook set: {url}")
    except NotifyError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_notify.command("show")
@click.argument("vault")
def notify_show(vault: str) -> None:
    """Show the configured webhook URL for VAULT."""
    url = get_webhook(vault)
    if url:
        click.echo(url)
    else:
        click.echo("No webhook configured.")


@cmd_notify.command("clear")
@click.argument("vault")
def notify_clear(vault: str) -> None:
    """Remove the webhook URL for VAULT."""
    clear_webhook(vault)
    click.echo("Webhook cleared.")


@cmd_notify.command("test")
@click.argument("vault")
@click.option("--action", default="test", show_default=True, help="Action label to include in the test payload.")
def notify_test(vault: str, action: str) -> None:
    """Send a test notification for VAULT."""
    ev = NotifyEvent(vault_path=vault, action=action, keys=[])
    try:
        sent = fire(ev)
        if sent:
            click.echo("Test notification sent.")
        else:
            click.echo("No webhook configured — nothing sent.")
    except NotifyError as exc:
        raise click.ClickException(str(exc)) from exc
