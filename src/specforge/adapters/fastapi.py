"""FastAPI adapter for SpecForge interactive documentation and contract testing."""

from typing import Any, Optional

try:
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
except ImportError:
    FastAPI = None  # type: ignore

from specforge.config import SpecForgeConfig
from specforge.parser.openapi3 import OpenAPIParser
from specforge.testing.exporters.pytest_export import PytestExporter
from specforge.testing.planner import TestPlanner
from specforge.utils.html_injector import render_html


class SpecForge:
    """Mounts the SpecForge interactive client and boundary test suite onto a FastAPI application."""

    def __init__(
        self,
        app: Any,
        path: str = "/docs",
        title: str = "SpecForge API Studio",
        spec_url: Optional[str] = None,
        theme: str = "dark",
        enable_tests: bool = True,
        disable_default_docs: bool = False,
        **kwargs: Any,
    ):
        if FastAPI is None:
            raise ImportError(
                "FastAPI is not installed. Install it with `pip install specforge[fastapi]`."
            )

        self.app = app
        self.path = path
        self.spec_url = spec_url or getattr(app, "openapi_url", "/openapi.json")

        self.config = SpecForgeConfig(
            title=title,
            path=path,
            spec_url=self.spec_url,
            theme=theme,  # type: ignore
            enable_tests=enable_tests,
            **kwargs,
        )

        if disable_default_docs and hasattr(app, "docs_url"):
            app.docs_url = None

        self._register_routes()

    def _register_routes(self) -> None:
        """Register the documentation UI and test plan endpoints on the FastAPI app."""

        @self.app.get(self.path, response_class=HTMLResponse, include_in_schema=False)
        async def specforge_docs_endpoint(request: Request) -> Response:
            html = render_html(self.config)
            return HTMLResponse(content=html)

        @self.app.get(
            "/specforge/api/plan",
            response_class=JSONResponse,
            include_in_schema=False,
        )
        async def specforge_test_plan_endpoint(request: Request) -> Response:
            # Generate or retrieve active OpenAPI specification
            raw_spec: dict[str, Any] = self.app.openapi()
            parser = OpenAPIParser(raw_spec)
            spec_model = parser.parse()

            plans = []
            for op in spec_model.operations:
                plan = TestPlanner.plan_operation_tests(op)
                plans.append(plan.to_dict())

            return JSONResponse(content={"plans": plans})

        @self.app.get(
            "/specforge/api/export-pytest",
            response_class=PlainTextResponse,
            include_in_schema=False,
        )
        async def specforge_export_pytest_endpoint(request: Request) -> Response:
            raw_spec: dict[str, Any] = self.app.openapi()
            parser = OpenAPIParser(raw_spec)
            spec_model = parser.parse()

            all_test_cases = []
            for op in spec_model.operations:
                plan = TestPlanner.plan_operation_tests(op)
                all_test_cases.extend(plan.test_cases)

            base_url = str(request.base_url).rstrip("/")
            code = PytestExporter.export(all_test_cases, base_url=base_url)
            return PlainTextResponse(
                content=code,
                headers={"Content-Disposition": 'attachment; filename="test_api_contracts.py"'},
            )
