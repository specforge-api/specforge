"""Normalized internal models for OpenAPI specs and schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ParameterLocation(str, Enum):
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"


@dataclass
class JSONSchema:
    """Represents a normalized JSON Schema / OpenAPI Schema object."""

    type: str | list[str] | None = None
    format: str | None = None
    title: str | None = None
    description: str | None = None
    default: Any | None = None
    example: Any | None = None
    enum: list[Any] | None = None

    # String constraints
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None

    # Numeric constraints
    minimum: int | float | None = None
    maximum: int | float | None = None
    exclusive_minimum: int | float | bool | None = None
    exclusive_maximum: int | float | bool | None = None
    multiple_of: int | float | None = None

    # Array constraints
    items: JSONSchema | None = None
    min_items: int | None = None
    max_items: int | None = None
    unique_items: bool | None = None

    # Object constraints
    properties: dict[str, JSONSchema] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    additional_properties: bool | JSONSchema = True

    # Polymorphism / Nullability
    nullable: bool = False
    all_of: list[JSONSchema] = field(default_factory=list)
    any_of: list[JSONSchema] = field(default_factory=list)
    one_of: list[JSONSchema] = field(default_factory=list)

    raw_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class Parameter:
    """Represents an API operation parameter (query, path, header, or cookie)."""

    name: str
    location: ParameterLocation
    required: bool = False
    description: str | None = None
    schema: JSONSchema | None = None
    example: Any | None = None


@dataclass
class RequestBody:
    """Represents an operation's HTTP request body definition."""

    description: str | None = None
    required: bool = False
    content_type: str = "application/json"
    schema: JSONSchema | None = None
    example: Any | None = None


@dataclass
class ResponseDefinition:
    """Represents an expected HTTP response definition."""

    status_code: str
    description: str = ""
    content_type: str = "application/json"
    schema: JSONSchema | None = None


@dataclass
class Operation:
    """Represents an HTTP endpoint operation (e.g. POST /users)."""

    method: str  # "get", "post", "put", "delete", "patch", etc.
    path: str
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    request_body: RequestBody | None = None
    responses: dict[str, ResponseDefinition] = field(default_factory=dict)

    @property
    def key(self) -> str:
        """Unique identifier key for this operation."""
        return f"{self.method.upper()} {self.path}"


@dataclass
class OpenAPISpec:
    """Normalized container for an entire API specification."""

    title: str = "API Documentation"
    version: str = "1.0.0"
    description: str = ""
    servers: list[str] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)
    raw_spec: dict[str, Any] = field(default_factory=dict)

    def get_operation(self, method: str, path: str) -> Operation | None:
        """Find an operation by method and path."""
        target_method = method.lower()
        for op in self.operations:
            if op.method.lower() == target_method and op.path == path:
                return op
        return None
