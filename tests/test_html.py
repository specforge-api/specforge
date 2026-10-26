"""Unit tests for HTML rendering and configuration injection."""

from specforge.config import SpecForgeConfig
from specforge.utils.html_injector import render_html


def test_render_html_injects_config():
    """Verify configuration is serialized and injected into the HTML asset."""
    config = SpecForgeConfig(
        title="Custom Test API Studio",
        theme="light",
        spec_url="/my-custom-openapi.json",
        enable_tests=True,
    )
    html = render_html(config)

    assert "<!DOCTYPE html>" in html
    assert "window.__SPECFORGE_CONFIG__" in html
    assert "Custom Test API Studio" in html
    assert "/my-custom-openapi.json" in html
    assert "light" in html
