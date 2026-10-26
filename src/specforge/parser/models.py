"""Normalized internal models for OpenAPI specs and schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ParameterLocation(str, Enum):
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"


@dataclass
class JSONSchema:
    """Represents a normalized JSON Schema / OpenAPI Schema object."""

    type: Optional[Union[str, List[str]]] = None
    format: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    example: Optional[Any] = None
    enum: Optional[List[Any]] = None

    # String constraints
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None

    # Numeric constraints
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    exclusive_minimum: Optional[Union[int, float, bool]] = None
    exclusive_maximum: Optional[Union[int, float, bool]] = None
    multiple_of: Optional[Union[int, float]] = None

    # Array constraints
    items: Optional[JSONSchema] = None
    min_items: Optional[int] = None
    max_items: Optional[int] = None
    unique_items: Optional[bool] = None

    # Object constraints
    properties: Dict[str, JSONSchema] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    additional_properties: Union[bool, JSONSchema] = True

    # Polymorphism / Nullability
    nullable: bool = False
    all_of: List[JSONSchema] = field(default_factory=list)
    any_of: List[JSONSchema] = field(default_factory=list)
    one_of: List[JSONSchema] = field(default_factory=list)

    raw_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Parameter:
    """Represents an API operation parameter (query, path, header, or cookie)."""

    name: str
    location: ParameterLocation
    required: bool = False
    description: Optional[str] = None
    schema: Optional[JSONSchema] = None
    example: Optional[Any] = None


@dataclass
class RequestBody:
    """Represents an operation's HTTP request body definition."""

    description: Optional[str] = None
    required: bool = False
    content_type: str = "application/json"
    schema: Optional[JSONSchema] = None
    example: Optional[Any] = None


@dataclass
class ResponseDefinition:
    """Represents an expected HTTP response definition."""

    status_code: str
    description: str = ""
    content_type: str = "application/json"
    schema: Optional[JSONSchema] = None


@dataclass
class Operation:
    """Represents an HTTP endpoint operation (e.g. POST /users)."""

    method: str  # "get", "post", "put", "delete", "patch", etc.
    path: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    responses: Dict[str, ResponseDefinition] = field(default_factory=dict)

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
    servers: List[str] = field(default_factory=list)
    operations: List[Operation] = field(default_factory=list)
    raw_spec: Dict[str, Any] = field(default_factory=dict)

    def get_operation(self, method: str, path: str) -> Optional[Operation]:
        """Find an operation by method and path."""
        target_method = method.lower()
        for op in self.operations:
            if op.method.lower() == target_method and op.path == path:
                return op
        return None
