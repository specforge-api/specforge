"""Injects configuration and specifications into the pre-compiled HTML asset."""

import json
from pathlib import Path
from typing import Any, Optional

from specforge.config import SpecForgeConfig


def get_asset_html_path() -> Path:
    """Return the filesystem path to the bundled index.html asset."""
    return Path(__file__).parent.parent / "assets" / "index.html"


def render_html(
    config: SpecForgeConfig,
    spec_dict: Optional[dict[str, Any]] = None,
) -> str:
    """Read the inlined HTML template and inject the runtime configuration and spec."""
    asset_path = get_asset_html_path()

    if not asset_path.exists():
        raise FileNotFoundError(
            f"SpecForge frontend asset not found at {asset_path}. "
            "Ensure the package was installed with assets bundled."
        )

    html_template = asset_path.read_text(encoding="utf-8")

    config_data = config.to_dict()
    if spec_dict is not None:
        config_data["embedded_spec"] = spec_dict

    config_json = json.dumps(config_data)
    replacement = f"<script>window.__SPECFORGE_CONFIG__ = {config_json};</script>"

    # Replace placeholder or insert into <head>
    if "<!-- __SPECFORGE_CONFIG_INJECTION__ -->" in html_template:
        return html_template.replace("<!-- __SPECFORGE_CONFIG_INJECTION__ -->", replacement)
    elif "</head>" in html_template:
        return html_template.replace("</head>", f"{replacement}\n</head>")
    else:
        return f"{replacement}\n{html_template}"
