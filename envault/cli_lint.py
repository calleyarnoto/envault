"""CLI command: envault lint."""
from __future__ import annotations

import sys
import click

from envault.cli import _get_vault
from envault.lint import LintError, lint_vault


@click.command("lint")
@click.option(
    "--vault",
    "vault_path",
    default=".envault",
    show_default=True,
    help="Path to the vault file.",
)
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase.")
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit with non-zero status if any issues are found.",
)
def cmd_lint(vault_path: str, passphrase: str, strict: bool) -> None:
    """Lint secrets in the vault against best-practice rules."""
    try:
        issues = lint_vault(vault_path, passphrase)
    except LintError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not issues:
        click.echo("\u2713 No issues found.")
        return

    click.echo(f"Found {len(issues)} issue(s):\n")
    for issue in issues:
        click.echo(f"  [{issue.rule}] {issue.message}")

    if strict:
        sys.exit(1)
