"""Tests for envault.env_audit_report."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import append as audit_append
from envault.env_audit_report import AuditReport, ReportError, build_audit_report
from envault.vault import Vault

PASSPHRASE = "audit-report-test"


@pytest.fixture()
def vault_file(tmp_path):
    vp = tmp_path / "test.vault"
    Vault.init(vp, PASSPHRASE)
    v = Vault.load(vp, PASSPHRASE)
    v.set("DB_URL", "postgres://localhost/db")
    v.set("API_KEY", "secret123")
    v.get("DB_URL")
    v.delete("API_KEY")
    return vp


def test_build_report_returns_audit_report(vault_file):
    report = build_audit_report(vault_file)
    assert isinstance(report, AuditReport)


def test_build_report_missing_vault_raises(tmp_path):
    with pytest.raises(ReportError, match="Vault not found"):
        build_audit_report(tmp_path / "missing.vault")


def test_total_reflects_all_entries(vault_file):
    report = build_audit_report(vault_file)
    # init + 2x set + get + delete = at least 5
    assert report.total >= 5


def test_filter_by_action(vault_file):
    report = build_audit_report(vault_file, filter_action="set")
    assert report.total == 2
    assert all(e.action == "set" for e in report.filtered)


def test_filter_by_key(vault_file):
    report = build_audit_report(vault_file, filter_key="DB_URL")
    for e in report.filtered:
        assert e.key == "DB_URL"


def test_filter_action_and_key_combined(vault_file):
    report = build_audit_report(vault_file, filter_action="get", filter_key="DB_URL")
    assert report.total == 1
    assert report.filtered[0].action == "get"
    assert report.filtered[0].key == "DB_URL"


def test_action_counts_dict(vault_file):
    report = build_audit_report(vault_file)
    counts = report.action_counts()
    assert isinstance(counts, dict)
    assert counts.get("set", 0) == 2
    assert counts.get("delete", 0) == 1


def test_summary_contains_total(vault_file):
    report = build_audit_report(vault_file)
    s = report.summary()
    assert f"total={report.total}" in s


def test_as_text_contains_vault_path(vault_file):
    report = build_audit_report(vault_file)
    text = report.as_text()
    assert str(vault_file) in text


def test_as_text_contains_actions(vault_file):
    report = build_audit_report(vault_file)
    text = report.as_text()
    assert "set" in text
    assert "delete" in text


def test_as_json_is_valid_json(vault_file):
    report = build_audit_report(vault_file)
    data = json.loads(report.as_json())
    assert isinstance(data, list)
    assert len(data) == report.total


def test_as_json_entries_have_action_field(vault_file):
    report = build_audit_report(vault_file)
    data = json.loads(report.as_json())
    for entry in data:
        assert "action" in entry
