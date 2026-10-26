"""SpecForge: The Interactive API Client & Automated Contract Testing Engine for Python."""

from specforge.config import SpecForgeConfig
from specforge.parser.openapi3 import OpenAPIParser
from specforge.testing.exporters.pytest_export import PytestExporter
from specforge.testing.planner import TestPlanner

__version__ = "0.1.0"

# Conditionally import FastAPI adapter if available
try:
    from specforge.adapters.fastapi import SpecForge
except ImportError:
    SpecForge = None  # type: ignore

__all__ = [
    "SpecForge",
    "SpecForgeConfig",
    "OpenAPIParser",
    "TestPlanner",
    "PytestExporter",
    "__version__",
]
