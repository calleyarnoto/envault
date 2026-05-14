"""Tests for envault.template."""

from __future__ import annotations

import pytest

from envault.template import TemplateError, render_template, render_file
from envault.vault import Vault


@pytest.fixture()
def vault(tmp_path):
    v = Vault(tmp_path / "vault.json")
    v.init("secret")
    v.set("DB_HOST", "localhost", "secret")
    v.set("DB_PASS", "s3cr3t!", "secret")
    v.set("API_KEY", "abc123", "secret")
    return v


def test_single_placeholder_replaced(vault):
    result = render_template("host={{ DB_HOST }}", vault, "secret")
    assert result == "host=localhost"


def test_multiple_placeholders_replaced(vault):
    tmpl = "host={{ DB_HOST }} pass={{ DB_PASS }}"
    result = render_template(tmpl, vault, "secret")
    assert result == "host=localhost pass=s3cr3t!"


def test_placeholder_without_spaces(vault):
    result = render_template("key={{API_KEY}}", vault, "secret")
    assert result == "key=abc123"


def test_unknown_key_strict_raises(vault):
    with pytest.raises(TemplateError, match="MISSING_KEY"):
        render_template("x={{ MISSING_KEY }}", vault, "secret")


def test_unknown_key_non_strict_leaves_placeholder(vault):
    result = render_template(
        "x={{ MISSING_KEY }}", vault, "secret", strict=False
    )
    assert "{{ MISSING_KEY }}" in result


def test_multiple_missing_keys_all_reported(vault):
    with pytest.raises(TemplateError) as exc_info:
        render_template(
            "{{ MISSING_A }} {{ MISSING_B }}", vault, "secret"
        )
    msg = str(exc_info.value)
    assert "MISSING_A" in msg
    assert "MISSING_B" in msg


def test_no_placeholders_returns_original(vault):
    tmpl = "no placeholders here"
    assert render_template(tmpl, vault, "secret") == tmpl


def test_wrong_passphrase_raises(vault):
    with pytest.raises(Exception):
        render_template("{{ DB_HOST }}", vault, "wrong")


def test_render_file_writes_output(vault, tmp_path):
    src = tmp_path / "config.tmpl"
    dst = tmp_path / "config.env"
    src.write_text("DB_HOST={{ DB_HOST }}\nAPI_KEY={{ API_KEY }}\n")

    count = render_file(str(src), str(dst), vault, "secret")

    assert count == 2
    content = dst.read_text()
    assert "DB_HOST=localhost" in content
    assert "API_KEY=abc123" in content


def test_render_file_returns_placeholder_count(vault, tmp_path):
    src = tmp_path / "t.tmpl"
    dst = tmp_path / "t.out"
    src.write_text("{{ DB_HOST }} {{ DB_HOST }} {{ DB_PASS }}")
    count = render_file(str(src), str(dst), vault, "secret")
    assert count == 3
