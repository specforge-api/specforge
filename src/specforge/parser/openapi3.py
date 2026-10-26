"""OpenAPI 3.x and Swagger 2.0 parser that outputs normalized OpenAPISpec models."""

from typing import Any, Dict, List, Optional

from specforge.parser.models import (
    JSONSchema,
    OpenAPISpec,
    Operation,
    Parameter,
    ParameterLocation,
    RequestBody,
    ResponseDefinition,
)
from specforge.parser.resolver import RefResolver


class OpenAPIParser:
    """Parses raw OpenAPI dictionaries into structured, dereferenced OpenAPISpec objects."""

    def __init__(self, raw_spec: Dict[str, Any]):
        self.raw_spec = raw_spec
        self.resolver = RefResolver(raw_spec)

    def parse(self) -> OpenAPISpec:
        """Execute full parsing of the OpenAPI specification."""
        info = self.raw_spec.get("info", {})
        title = info.get("title", "API Documentation")
        version = info.get("version", "1.0.0")
        description = info.get("description", "")

        servers: List[str] = []
        if "servers" in self.raw_spec and isinstance(self.raw_spec["servers"], list):
            for s in self.raw_spec["servers"]:
                if isinstance(s, dict) and "url" in s:
                    servers.append(s["url"])
        elif "host" in self.raw_spec:
            # Swagger 2.0 fallback
            schemes = self.raw_spec.get("schemes", ["http"])
            host = self.raw_spec["host"]
            base_path = self.raw_spec.get("basePath", "")
            servers.append(f"{schemes[0]}://{host}{base_path}")

        operations: List[Operation] = []
        paths = self.raw_spec.get("paths", {})

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            # Path-level parameters
            path_params = path_item.get("parameters", [])

            for method, op_data in path_item.items():
                if method.lower() not in (
                    "get", "post", "put", "delete", "patch", "options", "head", "trace"
                ):
                    continue
                if not isinstance(op_data, dict):
                    continue

                operation = self._parse_operation(path, method.lower(), op_data, path_params)
                operations.append(operation)

        return OpenAPISpec(
            title=title,
            version=version,
            description=description,
            servers=servers,
            operations=operations,
            raw_spec=self.raw_spec,
        )

    def _parse_operation(
        self,
        path: str,
        method: str,
        op_data: Dict[str, Any],
        path_level_params: List[Any],
    ) -> Operation:
        """Parse a single operation item."""
        summary = op_data.get("summary")
        description = op_data.get("description")
        operation_id = op_data.get("operationId")
        tags = op_data.get("tags", [])

        # Merge path-level and operation-level parameters
        merged_params_raw = list(path_level_params) + op_data.get("parameters", [])
        parameters: List[Parameter] = []

        for p_raw in merged_params_raw:
            derefed_param = self.resolver.dereference(p_raw)
            if not isinstance(derefed_param, dict) or "name" not in derefed_param:
                continue

            param_loc_str = derefed_param.get("in", "query")
            try:
                param_loc = ParameterLocation(param_loc_str)
            except ValueError:
                param_loc = ParameterLocation.QUERY

            schema_raw = derefed_param.get("schema", {})
            param_schema = self._parse_schema(schema_raw) if schema_raw else None

            parameters.append(
                Parameter(
                    name=derefed_param["name"],
                    location=param_loc,
                    required=derefed_param.get("required", False),
                    description=derefed_param.get("description"),
                    schema=param_schema,
                    example=derefed_param.get("example"),
                )
            )

        # Parse request body (OpenAPI 3.x)
        request_body: Optional[RequestBody] = None
        if "requestBody" in op_data:
            rb_raw = self.resolver.dereference(op_data["requestBody"])
            if isinstance(rb_raw, dict):
                content = rb_raw.get("content", {})
                content_type = "application/json"
                body_schema_raw = None

                if "application/json" in content:
                    content_type = "application/json"
                    body_schema_raw = content["application/json"].get("schema")
                elif content:
                    content_type = next(iter(content.keys()))
                    body_schema_raw = content[content_type].get("schema")

                parsed_schema = (
                    self._parse_schema(body_schema_raw) if body_schema_raw else None
                )
                request_body = RequestBody(
                    description=rb_raw.get("description"),
                    required=rb_raw.get("required", False),
                    content_type=content_type,
                    schema=parsed_schema,
                )

        # Parse responses
        responses: Dict[str, ResponseDefinition] = {}
        for status_code, resp_raw in op_data.get("responses", {}).items():
            derefed_resp = self.resolver.dereference(resp_raw)
            if not isinstance(derefed_resp, dict):
                continue

            resp_desc = derefed_resp.get("description", "")
            resp_content = derefed_resp.get("content", {})
            resp_schema = None
            resp_content_type = "application/json"

            if "application/json" in resp_content:
                resp_schema_raw = resp_content["application/json"].get("schema")
                if resp_schema_raw:
                    resp_schema = self._parse_schema(resp_schema_raw)
            elif resp_content:
                resp_content_type = next(iter(resp_content.keys()))
                resp_schema_raw = resp_content[resp_content_type].get("schema")
                if resp_schema_raw:
                    resp_schema = self._parse_schema(resp_schema_raw)

            responses[str(status_code)] = ResponseDefinition(
                status_code=str(status_code),
                description=resp_desc,
                content_type=resp_content_type,
                schema=resp_schema,
            )

        return Operation(
            method=method,
            path=path,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            parameters=parameters,
            request_body=request_body,
            responses=responses,
        )

    def _parse_schema(self, schema_raw: Any) -> JSONSchema:
        """Convert a raw dereferenced schema dictionary into a typed JSONSchema."""
        derefed = self.resolver.dereference(schema_raw)
        if not isinstance(derefed, dict):
            return JSONSchema(raw_schema={})

        schema_type = derefed.get("type")
        format_val = derefed.get("format")
        title = derefed.get("title")
        description = derefed.get("description")
        default = derefed.get("default")
        example = derefed.get("example")
        enum = derefed.get("enum")

        # String constraints
        min_length = derefed.get("minLength")
        max_length = derefed.get("maxLength")
        pattern = derefed.get("pattern")

        # Numeric constraints
        minimum = derefed.get("minimum")
        maximum = derefed.get("maximum")
        exclusive_minimum = derefed.get("exclusiveMinimum")
        exclusive_maximum = derefed.get("exclusiveMaximum")
        multiple_of = derefed.get("multipleOf")

        # Array constraints
        items_schema = None
        if "items" in derefed:
            items_schema = self._parse_schema(derefed["items"])
        min_items = derefed.get("minItems")
        max_items = derefed.get("maxItems")
        unique_items = derefed.get("uniqueItems")

        # Object constraints
        properties: Dict[str, JSONSchema] = {}
        for prop_name, prop_raw in derefed.get("properties", {}).items():
            properties[prop_name] = self._parse_schema(prop_raw)

        required = derefed.get("required", [])
        if not isinstance(required, list):
            required = []

        additional_properties_raw = derefed.get("additionalProperties", True)
        if isinstance(additional_properties_raw, dict):
            additional_properties = self._parse_schema(additional_properties_raw)
        else:
            additional_properties = bool(additional_properties_raw)

        nullable = bool(derefed.get("nullable", False))

        # Handle allOf merging if present
        all_of: List[JSONSchema] = []
        if "allOf" in derefed and isinstance(derefed["allOf"], list):
            all_of = [self._parse_schema(item) for item in derefed["allOf"]]
            # Inherit properties from allOf members
            for parent_schema in all_of:
                for k, v in parent_schema.properties.items():
                    if k not in properties:
                        properties[k] = v
                for req_item in parent_schema.required:
                    if req_item not in required:
                        required.append(req_item)

        any_of: List[JSONSchema] = []
        if "anyOf" in derefed and isinstance(derefed["anyOf"], list):
            any_of = [self._parse_schema(item) for item in derefed["anyOf"]]

        one_of: List[JSONSchema] = []
        if "oneOf" in derefed and isinstance(derefed["oneOf"], list):
            one_of = [self._parse_schema(item) for item in derefed["oneOf"]]

        return JSONSchema(
            type=schema_type,
            format=format_val,
            title=title,
            description=description,
            default=default,
            example=example,
            enum=enum,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            minimum=minimum,
            maximum=maximum,
            exclusive_minimum=exclusive_minimum,
            exclusive_maximum=exclusive_maximum,
            multiple_of=multiple_of,
            items=items_schema,
            min_items=min_items,
            max_items=max_items,
            unique_items=unique_items,
            properties=properties,
            required=required,
            additional_properties=additional_properties,
            nullable=nullable,
            all_of=all_of,
            any_of=any_of,
            one_of=one_of,
            raw_schema=derefed,
        )
