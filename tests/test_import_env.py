"""Tests for envault.import_env."""

from __future__ import annotations

import pytest

from envault.import_env import ImportError, import_into_vault, parse_dotenv
from envault.vault import Vault


# ---------------------------------------------------------------------------
# parse_dotenv
# ---------------------------------------------------------------------------

def test_parse_basic_assignment():
    result = parse_dotenv("KEY=value")
    assert result == {"KEY": "value"}


def test_parse_double_quoted_value():
    result = parse_dotenv('SECRET="hello world"')
    assert result["SECRET"] == "hello world"


def test_parse_single_quoted_value():
    result = parse_dotenv("TOKEN='abc123'")
    assert result["TOKEN"] == "abc123"


def test_parse_export_prefix():
    result = parse_dotenv("export API_KEY=xyz")
    assert result["API_KEY"] == "xyz"


def test_parse_comments_ignored():
    src = "# this is a comment\nKEY=val"
    result = parse_dotenv(src)
    assert "#" not in str(result)
    assert result["KEY"] == "val"


def test_parse_blank_lines_ignored():
    src = "\n\nKEY=val\n\n"
    assert parse_dotenv(src) == {"KEY": "val"}


def test_parse_multiple_keys():
    src = "A=1\nB=2\nC=3"
    assert parse_dotenv(src) == {"A": "1", "B": "2", "C": "3"}


def test_parse_empty_value():
    assert parse_dotenv("EMPTY=") == {"EMPTY": ""}


def test_parse_invalid_line_skipped():
    src = "not-valid-line\nKEY=ok"
    result = parse_dotenv(src)
    assert list(result.keys()) == ["KEY"]


# ---------------------------------------------------------------------------
# import_into_vault
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path):
    path = tmp_path / "test.vault"
    Vault.init(path, "pass")
    return path


def test_import_adds_keys(vault_file):
    report = import_into_vault(vault_file, "pass", "X=1\nY=2")
    statuses = {k: s for k, s in report}
    assert statuses["X"] == "imported"
    assert statuses["Y"] == "imported"


def test_import_values_readable(vault_file):
    import_into_vault(vault_file, "pass", "MY_KEY=secret")
    vault = Vault.load(vault_file, "pass")
    assert vault.get("MY_KEY") == "secret"


def test_import_skips_existing_by_default(vault_file):
    Vault.load(vault_file, "pass").set("KEY", "old") or None
    v = Vault.load(vault_file, "pass")
    v.set("KEY", "old")
    v.save("pass")

    report = import_into_vault(vault_file, "pass", "KEY=new")
    assert report[0] == ("KEY", "skipped")
    assert Vault.load(vault_file, "pass").get("KEY") == "old"


def test_import_overwrites_when_flag_set(vault_file):
    v = Vault.load(vault_file, "pass")
    v.set("KEY", "old")
    v.save("pass")

    report = import_into_vault(vault_file, "pass", "KEY=new", overwrite=True)
    assert report[0] == ("KEY", "overwritten")
    assert Vault.load(vault_file, "pass").get("KEY") == "new"


def test_import_raises_if_vault_missing(tmp_path):
    with pytest.raises(ImportError, match="Vault not found"):
        import_into_vault(tmp_path / "missing.vault", "pass", "K=v")


def test_import_empty_source_returns_empty_list(vault_file):
    assert import_into_vault(vault_file, "pass", "") == []
