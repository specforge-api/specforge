"""Configuration models for SpecForge."""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


@dataclass
class SpecForgeConfig:
    """Master configuration for SpecForge documentation and testing studio."""

    title: str = "SpecForge API Studio"
    path: str = "/docs"
    spec_url: Optional[str] = None
    theme: Literal["dark", "light", "auto"] = "dark"
    enable_tests: bool = True
    allow_mutation_fuzzing: bool = True
    fail_on_500: bool = True
    fail_on_leak: bool = True
    max_string_fuzz_length: int = 1000
    timeout_seconds: float = 10.0
    headers: dict[str, str] = field(default_factory=dict)
    custom_css: Optional[str] = None
    logo_url: Optional[str] = None
    export_pytest: bool = True
    enable_api_endpoints: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for injection into frontend client."""
        return {
            "title": self.title,
            "path": self.path,
            "spec_url": self.spec_url,
            "theme": self.theme,
            "enable_tests": self.enable_tests,
            "allow_mutation_fuzzing": self.allow_mutation_fuzzing,
            "fail_on_500": self.fail_on_500,
            "fail_on_leak": self.fail_on_leak,
            "max_string_fuzz_length": self.max_string_fuzz_length,
            "timeout_seconds": self.timeout_seconds,
            "headers": self.headers,
            "logo_url": self.logo_url,
            "export_pytest": self.export_pytest,
            "enable_api_endpoints": self.enable_api_endpoints,
        }
