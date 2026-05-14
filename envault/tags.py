"""Tag-based secret grouping and filtering for envault vaults."""

from __future__ import annotations

from typing import Dict, List, Optional


class TagError(Exception):
    """Raised when a tag operation fails."""


TAG_KEY = "__tags__"


def _load_tag_map(vault) -> Dict[str, List[str]]:
    """Return the tag map stored inside the vault, or an empty dict."""
    try:
        raw = vault.get(TAG_KEY)
    except Exception:
        return {}
    import json
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _save_tag_map(vault, tag_map: Dict[str, List[str]], passphrase: str) -> None:
    import json
    vault.set(TAG_KEY, json.dumps(tag_map), passphrase)


def add_tag(vault, key: str, tag: str, passphrase: str) -> None:
    """Add *tag* to *key*.  Creates the tag map entry if absent."""
    if not tag:
        raise TagError("Tag must not be empty.")
    tag_map = _load_tag_map(vault)
    tags = tag_map.get(key, [])
    if tag not in tags:
        tags.append(tag)
    tag_map[key] = tags
    _save_tag_map(vault, tag_map, passphrase)


def remove_tag(vault, key: str, tag: str, passphrase: str) -> bool:
    """Remove *tag* from *key*.  Returns True if the tag was present."""
    tag_map = _load_tag_map(vault)
    tags = tag_map.get(key, [])
    if tag not in tags:
        return False
    tags.remove(tag)
    tag_map[key] = tags
    _save_tag_map(vault, tag_map, passphrase)
    return True


def list_tags(vault, key: str) -> List[str]:
    """Return all tags assigned to *key*."""
    return _load_tag_map(vault).get(key, [])


def keys_for_tag(vault, tag: str) -> List[str]:
    """Return all secret keys that carry *tag*."""
    tag_map = _load_tag_map(vault)
    return [k for k, tags in tag_map.items() if tag in tags]


def all_tags(vault) -> Dict[str, List[str]]:
    """Return the full tag map (key -> list of tags), excluding internal keys."""
    return {k: v for k, v in _load_tag_map(vault).items() if k != TAG_KEY}
