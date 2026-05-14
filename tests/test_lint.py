"""Tests for envault.lint."""
import json
import pytest

from envault.vault import Vault
from envault.lint import LintIssue, LintError, lint_vault


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.env")
    Vault.init(path, "passphrase")
    return path


def _add(vault_file, key, value):
    v = Vault.load(vault_file, "passphrase")
    v.set(key, value)
    v.save()


# ---------------------------------------------------------------------------
# empty_value rule
# ---------------------------------------------------------------------------

def test_empty_value_flagged(vault_file):
    _add(vault_file, "MY_SECRET", "")
    issues = lint_vault(vault_file, "passphrase")
    rules = [i.rule for i in issues]
    assert "empty_value" in rules


# ---------------------------------------------------------------------------
# weak_value rule
# ---------------------------------------------------------------------------

def test_weak_value_flagged(vault_file):
    _add(vault_file, "MY_TOKEN", "password")
    issues = lint_vault(vault_file, "passphrase")
    rules = [i.rule for i in issues]
    assert "weak_value" in rules


def test_strong_value_not_flagged_as_weak(vault_file):
    _add(vault_file, "MY_TOKEN", "xK9!mP2@qR5$")
    issues = lint_vault(vault_file, "passphrase")
    rules = [i.rule for i in issues]
    assert "weak_value" not in rules


# ---------------------------------------------------------------------------
# short_value rule
# ---------------------------------------------------------------------------

def test_short_value_flagged(vault_file):
    _add(vault_file, "API_KEY", "abc")
    issues = lint_vault(vault_file, "passphrase")
    rules = [i.rule for i in issues]
    assert "short_value" in rules


def test_value_at_min_length_not_flagged(vault_file):
    _add(vault_file, "API_KEY", "abcdefgh")  # exactly 8 chars
    issues = lint_vault(vault_file, "passphrase")
    rules = [i.rule for i in issues]
    assert "short_value" not in rules


# ---------------------------------------------------------------------------
# key_naming rule
# ---------------------------------------------------------------------------

def test_lowercase_key_flagged(vault_file):
    _add(vault_file, "my_secret", "strongvalue123")
    issues = lint_vault(vault_file, "passphrase")
    matching = [i for i in issues if i.key == "my_secret" and i.rule == "key_naming"]
    assert matching


def test_upper_snake_key_not_flagged(vault_file):
    _add(vault_file, "MY_SECRET_KEY", "strongvalue123")
    issues = lint_vault(vault_file, "passphrase")
    naming_issues = [i for i in issues if i.key == "MY_SECRET_KEY" and i.rule == "key_naming"]
    assert not naming_issues


# ---------------------------------------------------------------------------
# LintError
# ---------------------------------------------------------------------------

def test_lint_missing_vault_raises(tmp_path):
    with pytest.raises(LintError):
        lint_vault(str(tmp_path / "missing.env"), "passphrase")


def test_lint_wrong_passphrase_raises(vault_file):
    with pytest.raises(LintError):
        lint_vault(vault_file, "wrong")


# ---------------------------------------------------------------------------
# LintIssue dataclass
# ---------------------------------------------------------------------------

def test_lint_issue_fields():
    issue = LintIssue(key="FOO", rule="empty_value", message="msg")
    assert issue.key == "FOO"
    assert issue.rule == "empty_value"
    assert issue.message == "msg"
