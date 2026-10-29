"""Flask adapter for SpecForge interactive documentation and contract testing."""

from typing import Any, Optional

try:
    from flask import (  # type: ignore
        Blueprint,
        Flask,
        Response,
        jsonify,
    )
except ImportError:
    Flask = None  # type: ignore

from specforge.config import SpecForgeConfig
from specforge.parser.openapi3 import OpenAPIParser
from specforge.testing.planner import TestPlanner
from specforge.utils.html_injector import render_html


class SpecForge:
    """Mounts the SpecForge interactive client and boundary test suite onto a Flask application."""

    def __init__(
        self,
        app: Any,
        path: str = "/docs",
        spec_url: str = "/api/spec.json",
        title: str = "SpecForge API Studio",
        theme: str = "dark",
        enable_tests: bool = True,
        enable_api_endpoints: bool = True,
        spec_dict: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        if Flask is None:
            raise ImportError("Flask is not installed. Install it with `pip install specforge[flask]`.")

        self.app = app
        self.path = path
        self.spec_url = spec_url
        self.spec_dict = spec_dict

        self.config = SpecForgeConfig(
            title=title,
            path=path,
            spec_url=spec_url,
            theme=theme,  # type: ignore
            enable_tests=enable_tests,
            enable_api_endpoints=enable_api_endpoints,
            **kwargs,
        )

        self._register_blueprint()

    def _register_blueprint(self) -> None:
        """Register the Flask blueprint."""
        bp = Blueprint("specforge", __name__)

        @bp.route(self.path, methods=["GET"])
        def specforge_docs() -> Any:
            html = render_html(self.config, self.spec_dict)
            return Response(html, mimetype="text/html")

        if self.config.enable_api_endpoints:
            @bp.route("/specforge/api/plan", methods=["GET"])
            def specforge_plan() -> Any:
                if not self.spec_dict:
                    return jsonify({"error": "SpecForge Flask adapter requires spec_dict for test planning."}), 400

                parser = OpenAPIParser(self.spec_dict)
                spec_model = parser.parse()

                plans = []
                for op in spec_model.operations:
                    plan = TestPlanner.plan_operation_tests(op)
                    plans.append(plan.to_dict())

                return jsonify({"plans": plans})

        self.app.register_blueprint(bp)
