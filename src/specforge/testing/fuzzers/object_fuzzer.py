"""Object schema mutation and required field omission generator."""

import copy
from typing import Any

from specforge.parser.models import JSONSchema


class ObjectFuzzer:
    """Generates mutations for object schemas (request bodies and nested objects)."""

    @classmethod
    def generate_valid_baseline(cls, schema: JSONSchema) -> dict[str, Any]:
        """Generate a valid baseline dictionary conforming to the schema."""
        baseline: dict[str, Any] = {}

        for prop_name, prop_schema in schema.properties.items():
            if prop_schema.example is not None:
                baseline[prop_name] = prop_schema.example
            elif prop_schema.default is not None:
                baseline[prop_name] = prop_schema.default
            elif prop_schema.enum:
                baseline[prop_name] = prop_schema.enum[0]
            elif prop_schema.type == "string":
                if prop_schema.format == "email":
                    baseline[prop_name] = "user@example.com"
                elif prop_schema.format == "uuid":
                    baseline[prop_name] = "123e4567-e89b-12d3-a456-426614174000"
                elif prop_schema.format in ("date-time", "date"):
                    baseline[prop_name] = "2026-01-01T12:00:00Z"
                else:
                    baseline[prop_name] = f"sample_{prop_name}"
            elif prop_schema.type == "integer":
                min_val = prop_schema.minimum if prop_schema.minimum is not None else 1
                baseline[prop_name] = int(min_val)
            elif prop_schema.type == "number":
                min_val = prop_schema.minimum if prop_schema.minimum is not None else 1.0
                baseline[prop_name] = float(min_val)
            elif prop_schema.type == "boolean":
                baseline[prop_name] = True
            elif prop_schema.type == "array":
                baseline[prop_name] = []
            elif prop_schema.type == "object":
                baseline[prop_name] = cls.generate_valid_baseline(prop_schema)
            else:
                baseline[prop_name] = "valid_value"

        return baseline

    @classmethod
    def generate_object_mutations(
        cls,
        schema: JSONSchema,
        baseline_payload: dict[str, Any],
    ) -> list[tuple[str, str, Any, str]]:
        """Generate object-level mutations (omissions, unexpected properties, type inversion)."""
        mutations: list[tuple[str, str, Any, str]] = []

        # 1. Combinatorial omission of required fields
        for req_field in schema.required:
            if req_field in baseline_payload:
                omitted_payload = copy.deepcopy(baseline_payload)
                del omitted_payload[req_field]
                mutations.append((
                    f"Structure: Omit Required Field '{req_field}'",
                    f"Reject payload missing required property '{req_field}'",
                    omitted_payload,
                    "Structure",
                ))

        # 2. Completely empty dictionary when required fields exist
        if schema.required:
            mutations.append((
                "Structure: Empty Object Payload",
                "Reject completely empty object {} when required properties exist",
                {},
                "Structure",
            ))

        # 3. Unexpected property injection when additionalProperties is False
        if schema.additional_properties is False:
            extra_payload = copy.deepcopy(baseline_payload)
            extra_payload["__unexpected_field__"] = "invalid"
            mutations.append((
                "Structure: Unexpected Additional Property",
                "Reject unlisted property when additionalProperties is false",
                extra_payload,
                "Structure",
            ))

        # 4. Type inversion: Primitive scalar instead of object dictionary
        mutations.append((
            "Type: String Instead of Object",
            "Reject string primitive instead of JSON dictionary object",
            "invalid_raw_string_payload",
            "Type",
        ))

        return mutations
