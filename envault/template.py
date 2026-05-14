"""Template rendering: substitute vault secrets into template strings."""

from __future__ import annotations

import re
from typing import Dict, Optional

from envault.vault import Vault, VaultError

__all__ = ["TemplateError", "render_template", "render_file"]

# Matches {{ KEY }} or {{KEY}} with optional whitespace
_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""


def render_template(
    template: str,
    vault: Vault,
    passphrase: str,
    *,
    strict: bool = True,
) -> str:
    """Replace ``{{ KEY }}`` placeholders in *template* with vault secrets.

    Parameters
    ----------
    template:
        Raw template string containing ``{{ KEY }}`` placeholders.
    vault:
        An open :class:`~envault.vault.Vault` instance.
    passphrase:
        Passphrase used to decrypt secrets.
    strict:
        When *True* (default), raise :class:`TemplateError` for any
        placeholder whose key is not found in the vault.  When *False*,
        leave unresolved placeholders unchanged.
    """
    missing: list[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        try:
            return vault.get(key, passphrase)
        except VaultError:
            if strict:
                missing.append(key)
                return match.group(0)  # keep original while collecting all
            return match.group(0)

    result = _PLACEHOLDER_RE.sub(_replace, template)

    if strict and missing:
        keys = ", ".join(sorted(missing))
        raise TemplateError(
            f"Template references unknown vault key(s): {keys}"
        )

    return result


def render_file(
    src_path: str,
    dst_path: str,
    vault: Vault,
    passphrase: str,
    *,
    strict: bool = True,
) -> int:
    """Read *src_path*, render placeholders, write result to *dst_path*.

    Returns the number of substitutions made.
    """
    with open(src_path, "r", encoding="utf-8") as fh:
        template = fh.read()

    placeholder_count = len(_PLACEHOLDER_RE.findall(template))
    rendered = render_template(template, vault, passphrase, strict=strict)

    with open(dst_path, "w", encoding="utf-8") as fh:
        fh.write(rendered)

    return placeholder_count
