"""Export vault secrets to various formats for CI/shell integration."""

from __future__ import annotations

from typing import Dict


SUPPORTED_FORMATS = ("dotenv", "shell", "github_actions", "json")


class ExportError(Exception):
    """Raised when export fails due to unsupported format or bad data."""


def export_secrets(secrets: Dict[str, str], fmt: str) -> str:
    """Render *secrets* as a string in the requested *fmt*.

    Parameters
    ----------
    secrets:
        Mapping of environment variable names to their plaintext values.
    fmt:
        One of ``dotenv``, ``shell``, ``github_actions``, or ``json``.

    Returns
    -------
    str
        The formatted output ready to be written to a file or stdout.

    Raises
    ------
    ExportError
        If *fmt* is not supported.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )

    if fmt == "dotenv":
        return _to_dotenv(secrets)
    if fmt == "shell":
        return _to_shell(secrets)
    if fmt == "github_actions":
        return _to_github_actions(secrets)
    if fmt == "json":
        return _to_json(secrets)

    raise ExportError(f"Unhandled format: {fmt}")  # pragma: no cover


def _to_dotenv(secrets: Dict[str, str]) -> str:
    lines = []
    for key, value in sorted(secrets.items()):
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def _to_shell(secrets: Dict[str, str]) -> str:
    lines = []
    for key, value in sorted(secrets.items()):
        escaped = value.replace("'", "'\"'\"'")
        lines.append(f"export {key}='{escaped}'")
    return "\n".join(lines) + ("\n" if lines else "")


def _to_github_actions(secrets: Dict[str, str]) -> str:
    """Produce ``echo "KEY=VALUE" >> $GITHUB_ENV`` lines.

    Note: values containing newlines are written using the GitHub Actions
    multiline syntax (``KEY<<EOF`` / ``EOF`` delimiter) to avoid truncation.
    """
    lines = []
    for key, value in sorted(secrets.items()):
        if "\n" in value:
            lines.append(f"{key}<<EOF")
            lines.append(value)
            lines.append("EOF")
        else:
            lines.append(f'echo "{key}={value}" >> $GITHUB_ENV')
    return "\n".join(lines) + ("\n" if lines else "")


def _to_json(secrets: Dict[str, str]) -> str:
    import json
    return json.dumps(secrets, indent=2, sort_keys=True) + "\n"
