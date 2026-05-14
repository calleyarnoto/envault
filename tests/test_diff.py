"""Tests for envault.diff module."""

from __future__ import annotations

import pytest

from envault.diff import DiffError, SecretDiff, diff_secrets, diff_snapshot_vs_vault


# ---------------------------------------------------------------------------
# diff_secrets unit tests
# ---------------------------------------------------------------------------

def test_added_key_detected():
    result = diff_secrets({}, {"NEW_KEY": "value"})
    assert len(result) == 1
    assert result[0].status == "added"
    assert result[0].key == "NEW_KEY"
    assert result[0].new_value == "value"
    assert result[0].old_value is None


def test_removed_key_detected():
    result = diff_secrets({"OLD_KEY": "val"}, {})
    assert len(result) == 1
    assert result[0].status == "removed"
    assert result[0].old_value == "val"


def test_changed_key_detected():
    result = diff_secrets({"K": "old"}, {"K": "new"})
    assert len(result) == 1
    assert result[0].status == "changed"
    assert result[0].old_value == "old"
    assert result[0].new_value == "new"


def test_unchanged_key_excluded_by_default():
    result = diff_secrets({"K": "same"}, {"K": "same"})
    assert result == []


def test_unchanged_key_included_when_requested():
    result = diff_secrets({"K": "same"}, {"K": "same"}, show_unchanged=True)
    assert len(result) == 1
    assert result[0].status == "unchanged"


def test_results_sorted_by_key():
    old = {"Z": "1", "A": "1"}
    new = {"Z": "1", "B": "2"}
    result = diff_secrets(old, new)
    keys = [d.key for d in result]
    assert keys == sorted(keys)


def test_empty_dicts_produce_no_diff():
    assert diff_secrets({}, {}) == []


# ---------------------------------------------------------------------------
# SecretDiff repr
# ---------------------------------------------------------------------------

def test_repr_added():
    assert repr(SecretDiff(key="K", status="added")) == "+ K"


def test_repr_removed():
    assert repr(SecretDiff(key="K", status="removed")) == "- K"


def test_repr_changed():
    assert repr(SecretDiff(key="K", status="changed")) == "~ K"


def test_repr_unchanged():
    assert repr(SecretDiff(key="K", status="unchanged")) == "  K"


# ---------------------------------------------------------------------------
# diff_snapshot_vs_vault integration
# ---------------------------------------------------------------------------

def test_diff_snapshot_vs_vault_bad_snapshot_raises(tmp_path):
    with pytest.raises(DiffError, match="Could not load snapshot"):
        diff_snapshot_vs_vault(
            str(tmp_path / "missing.snap"),
            str(tmp_path / "vault.json"),
            "passphrase",
        )


def test_diff_snapshot_vs_vault_bad_vault_raises(tmp_path, monkeypatch):
    """Snapshot loads fine but vault path is invalid."""
    monkeypatch.setattr(
        "envault.diff.restore_snapshot",
        lambda *a, **kw: {"KEY": "val"},
    )
    with pytest.raises(DiffError, match="Could not load vault"):
        diff_snapshot_vs_vault(
            str(tmp_path / "snap"),
            str(tmp_path / "nonexistent_vault.json"),
            "passphrase",
        )
