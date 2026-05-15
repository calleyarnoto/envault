"""Tests for envault.env_diff_report."""

from __future__ import annotations

import pytest

from envault.env_diff_report import (
    DiffReport,
    ReportError,
    build_report,
    report_vault_vs_dict,
)
from envault.vault import Vault


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path):
    path = tmp_path / "vault.env"
    v = Vault(path)
    v.init("secret")
    v.set("API_KEY", "abc123", "secret")
    v.set("DB_URL", "postgres://localhost/db", "secret")
    return path


@pytest.fixture()
def old_secrets():
    return {"API_KEY": "old_key", "DB_URL": "old_url", "KEEP": "same"}


@pytest.fixture()
def new_secrets():
    return {"API_KEY": "new_key", "KEEP": "same", "NEW_VAR": "hello"}


# ---------------------------------------------------------------------------
# build_report
# ---------------------------------------------------------------------------

def test_build_report_added(old_secrets, new_secrets):
    report = build_report(old_secrets, new_secrets)
    keys = [d.key for d in report.added]
    assert "NEW_VAR" in keys


def test_build_report_removed(old_secrets, new_secrets):
    report = build_report(old_secrets, new_secrets)
    keys = [d.key for d in report.removed]
    assert "DB_URL" in keys


def test_build_report_changed(old_secrets, new_secrets):
    report = build_report(old_secrets, new_secrets)
    keys = [d.key for d in report.changed]
    assert "API_KEY" in keys


def test_build_report_unchanged(old_secrets, new_secrets):
    report = build_report(old_secrets, new_secrets, include_unchanged=True)
    keys = [d.key for d in report.unchanged]
    assert "KEEP" in keys


def test_total_changes(old_secrets, new_secrets):
    report = build_report(old_secrets, new_secrets)
    assert report.total_changes == 3  # added 1, removed 1, changed 1


# ---------------------------------------------------------------------------
# DiffReport.summary / as_text
# ---------------------------------------------------------------------------

def test_summary_contains_counts(old_secrets, new_secrets):
    report = build_report(old_secrets, new_secrets)
    summary = report.summary()
    assert "Added" in summary
    assert "Removed" in summary
    assert "Changed" in summary


def test_as_text_no_changes():
    report = build_report({"A": "1"}, {"A": "1"})
    assert report.as_text() == "No changes detected."


def test_as_text_shows_plus_prefix(old_secrets, new_secrets):
    report = build_report(old_secrets, new_secrets)
    text = report.as_text()
    assert any(line.startswith("+") for line in text.splitlines())


def test_as_text_show_values_includes_value(old_secrets, new_secrets):
    report = build_report(old_secrets, new_secrets)
    text = report.as_text(show_values=True)
    assert "new_key" in text


# ---------------------------------------------------------------------------
# report_vault_vs_dict
# ---------------------------------------------------------------------------

def test_report_vault_vs_dict(vault_file):
    vault = Vault(vault_file)
    reference = {"API_KEY": "old", "EXTRA": "gone"}
    report = report_vault_vs_dict(vault, "secret", reference)
    assert report.total_changes > 0


def test_report_vault_vs_dict_wrong_passphrase_raises(vault_file):
    vault = Vault(vault_file)
    with pytest.raises(ReportError):
        report_vault_vs_dict(vault, "wrong", {})
