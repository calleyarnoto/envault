"""Tests for envault.export module."""

import json
import pytest

from envault.export import export_secrets, ExportError, SUPPORTED_FORMATS


SAMPLE = {
    "DB_PASSWORD": "s3cr3t",
    "API_KEY": "abc123",
    "GREETING": 'say "hello"',
}


def test_supported_formats_constant():
    assert "dotenv" in SUPPORTED_FORMATS
    assert "shell" in SUPPORTED_FORMATS
    assert "github_actions" in SUPPORTED_FORMATS
    assert "json" in SUPPORTED_FORMATS


def test_unsupported_format_raises():
    with pytest.raises(ExportError, match="Unsupported format"):
        export_secrets({"KEY": "val"}, "xml")


def test_dotenv_format_basic():
    result = export_secrets({"FOO": "bar"}, "dotenv")
    assert 'FOO="bar"' in result


def test_dotenv_format_escapes_double_quotes():
    result = export_secrets({"MSG": 'say "hi"'}, "dotenv")
    assert 'MSG="say \\"hi\\""' in result


def test_dotenv_format_sorted_keys():
    result = export_secrets(SAMPLE, "dotenv")
    lines = [l for l in result.splitlines() if l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys)


def test_dotenv_ends_with_newline():
    result = export_secrets({"X": "1"}, "dotenv")
    assert result.endswith("\n")


def test_shell_format_uses_export():
    result = export_secrets({"FOO": "bar"}, "shell")
    assert "export FOO='bar'" in result


def test_shell_format_escapes_single_quotes():
    result = export_secrets({"V": "it's"}, "shell")
    assert "it'\"'\"'s" in result


def test_github_actions_format():
    result = export_secrets({"TOKEN": "xyz"}, "github_actions")
    assert 'echo "TOKEN=xyz" >> $GITHUB_ENV' in result


def test_json_format_is_valid_json():
    result = export_secrets(SAMPLE, "json")
    parsed = json.loads(result)
    assert parsed["API_KEY"] == "abc123"
    assert parsed["DB_PASSWORD"] == "s3cr3t"


def test_json_format_sorted_keys():
    result = export_secrets(SAMPLE, "json")
    parsed = json.loads(result)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_empty_secrets_dotenv():
    result = export_secrets({}, "dotenv")
    assert result == ""


def test_empty_secrets_json():
    result = export_secrets({}, "json")
    assert json.loads(result) == {}
