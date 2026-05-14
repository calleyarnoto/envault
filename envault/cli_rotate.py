"""CLI sub-command: envault rotate."""

from __future__ import annotations

import click

from envault.audit import AuditLog
from envault.cli import _get_vault
from envault.rotate import RotationError, rotate_passphrase


@click.command("rotate")
@click.option(
    "--vault",
    "vault_path",
    default=".envault",
    show_default=True,
    help="Path to the vault file.",
)
@click.option(
    "--audit-log",
    "audit_log_path",
    default=None,
    help="Optional path to the audit log file.",
)
@click.password_option(
    "--old-passphrase",
    prompt="Current passphrase",
    confirmation_prompt=False,
    help="Current vault passphrase.",
)
@click.password_option(
    "--new-passphrase",
    prompt="New passphrase",
    help="New passphrase to encrypt the vault with.",
)
def cmd_rotate(
    vault_path: str,
    audit_log_path: str | None,
    old_passphrase: str,
    new_passphrase: str,
) -> None:
    """Re-encrypt the vault with a new passphrase."""
    from pathlib import Path

    path = Path(vault_path)
    log: AuditLog | None = None
    if audit_log_path:
        log = AuditLog(Path(audit_log_path))

    try:
        count = rotate_passphrase(
            path,
            old_passphrase,
            new_passphrase,
            audit_log=log,
            actor="cli",
        )
    except RotationError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Rotated passphrase. {count} secret(s) re-encrypted.")
