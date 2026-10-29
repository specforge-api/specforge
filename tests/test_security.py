"""Security regression tests for SpecForge.

Tests coverage:
- SEC-001: XSS via </script> breakout in HTML configuration & spec injection
- SEC-002: Code injection via PytestExporter string formatting
- SEC-003: SSRF scheme validation, metadata IP blocking, and spec size limits
- SEC-004: Toggling and protection of /specforge/api/* endpoints
- SEC-009: Shell escaping in build_curl_command
"""

import tempfile
from pathlib import Path

import pytest

from specforge.cli.main import MAX_SPEC_SIZE, _validate_spec_url, fetch_spec
from specforge.config import SpecForgeConfig
from specforge.testing.exporters.pytest_export import PytestExporter
from specforge.testing.invariants import TestCase as SpecTestCase
from specforge.testing.invariants import build_curl_command
from specforge.utils.html_injector import _html_safe_json, render_html

# --- SEC-001: XSS Neutralization Tests ---

def test_xss_script_breakout_in_config_title():
    """SEC-001: Verify </script> sequences in config values are escaped."""
    config = SpecForgeConfig(title='</script><script>alert("xss")</script>')
    html = render_html(config)

    assert '</script><script>' not in html
    assert '\\u003c/script\\u003e' in html
    assert 'window.__SPECFORGE_CONFIG__' in html


def test_xss_script_breakout_in_spec_dict():
    """SEC-001: Verify spec dict values with </script> are escaped."""
    spec = {"info": {"title": '</script><img src=x onerror=alert(1)>'}}
    config = SpecForgeConfig()
    html = render_html(config, spec_dict=spec)

    assert '</script><img' not in html
    assert '\\u003c/script\\u003e' in html


def test_html_safe_json_escapes_brackets_and_ampersand():
    """SEC-001: Unit test for _html_safe_json function."""
    payload = {"xss": "<script>alert('test & 1')</script>"}
    escaped = _html_safe_json(payload)

    assert "<" not in escaped
    assert ">" not in escaped
    assert "&" not in escaped
    assert "\\u003c" in escaped
    assert "\\u003e" in escaped
    assert "\\u0026" in escaped


# --- SEC-002: Python Code Injection in PytestExporter Tests ---

def test_code_injection_in_endpoint_path():
    """SEC-002: Verify malicious endpoint paths cannot inject Python code in exports."""
    tc = SpecTestCase(
        id="test_exploit",
        endpoint='/")\nimport os; os.system("calc")  #',
        method="get",
        field_name="username",
        mutation_category="Injection",
        mutation_name="CodeInjection",
        description="Path with code injection payload",
        payload={"dummy": 123},
    )
    code = PytestExporter.export([tc], base_url="http://testserver")

    # The generated Python code MUST be syntactically valid
    compiled = compile(code, "<test_export>", "exec")
    assert compiled is not None

    # The literal payload must be quoted and escaped, not executed as top-level code
    assert '\nimport os; os.system("calc")' not in code


def test_code_injection_in_method_and_base_url():
    """SEC-002: Verify malicious HTTP methods or base URLs cannot break Python syntax."""
    tc = SpecTestCase(
        id="test_method_inject",
        endpoint="/api/v1/resource",
        method='GET", None, None, 200, True, "x"),\n(__import__("os").system("id"),"',
        field_name="x",
        mutation_category="Category",
        mutation_name="Name",
        description='Desc with quotes " and \n newlines',
        payload=None,
    )
    code = PytestExporter.export([tc], base_url='http://localhost:8000"\nimport sys; sys.exit(1)#')

    # Must compile cleanly
    compiled = compile(code, "<test_export>", "exec")
    assert compiled is not None
    assert '\nimport sys; sys.exit(1)#' not in code


# --- SEC-003: SSRF & CLI Spec Fetcher Security Tests ---

def test_fetch_spec_blocks_unsupported_schemes():
    """SEC-003: Verify file://, ftp://, and gopher:// URLs are rejected."""
    with pytest.raises(ValueError, match="Unsupported URL scheme"):
        fetch_spec("file:///etc/passwd")

    with pytest.raises(ValueError, match="Unsupported URL scheme"):
        fetch_spec("ftp://example.com/spec.json")

    with pytest.raises(ValueError, match="Unsupported URL scheme"):
        fetch_spec("gopher://example.com/spec.json")


def test_fetch_spec_blocks_cloud_metadata_ip():
    """SEC-003: Verify cloud metadata link-local IP (169.254.169.254) is rejected."""
    with pytest.raises(ValueError, match="blocked for security"):
        _validate_spec_url("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(ValueError, match="blocked for security"):
        fetch_spec("http://169.254.169.254/computeMetadata/v1/")


def test_fetch_spec_enforces_max_size_on_local_file():
    """SEC-003: Verify oversized specification files are rejected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # Create a file that exceeds MAX_SPEC_SIZE
        f.seek(MAX_SPEC_SIZE + 10)
        f.write(" ")
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="maximum allowed size"):
            fetch_spec(temp_path)
    finally:
        Path(temp_path).unlink(missing_ok=True)


# --- SEC-009: Shell Escaping in build_curl_command Tests ---

def test_curl_command_escapes_single_quotes_and_special_chars():
    """SEC-009: Verify curl command properly quotes URLs, headers, and payloads."""
    tc = SpecTestCase(
        id="test_curl",
        endpoint="/users/test'; rm -rf / #",
        method="post",
        field_name="data",
        mutation_category="Test",
        mutation_name="Test",
        description="test",
        payload={"key": "val'; cat /etc/passwd"},
        headers={"X-Custom-Header": "val'; echo injected #"},
    )
    curl = build_curl_command(tc, base_url="http://localhost:8000")

    # Command should contain properly quoted arguments without bare unescaped semicolons or quotes
    assert "test'; rm -rf / #" not in curl
    assert "val'; echo injected #" not in curl


# --- SEC-004: API Endpoints Toggle Tests ---

def test_config_enable_api_endpoints_default():
    """SEC-004: Verify enable_api_endpoints defaults to True and can be set to False."""
    default_config = SpecForgeConfig()
    assert default_config.enable_api_endpoints is True
    assert default_config.to_dict()["enable_api_endpoints"] is True

    custom_config = SpecForgeConfig(enable_api_endpoints=False)
    assert custom_config.enable_api_endpoints is False
    assert custom_config.to_dict()["enable_api_endpoints"] is False
