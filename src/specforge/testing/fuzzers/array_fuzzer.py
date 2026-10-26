"""Array field mutation test generator."""

from typing import Any, List, Tuple

from specforge.parser.models import JSONSchema


class ArrayFuzzer:
    """Generates boundary and mutation payloads for array schema fields."""

    @classmethod
    def generate_mutations(
        cls,
        field_name: str,
        schema: JSONSchema,
        valid_example: Any = None,
    ) -> List[Tuple[str, str, Any, str]]:
        """Generate mutations for array field."""
        mutations: List[Tuple[str, str, Any, str]] = []

        # 1. Empty array check when minItems >= 1
        if schema.min_items is not None and schema.min_items > 0:
            mutations.append((
                "Boundary: Empty Array",
                f"Reject empty list [] for '{field_name}' (requires at least {schema.min_items})",
                [],
                "Boundary",
            ))

        # 2. Exceeding maxItems
        if schema.max_items is not None:
            mutations.append((
                "Boundary: Exceeds Max Items",
                f"Reject array with {schema.max_items + 1} items (> max {schema.max_items}) for '{field_name}'",
                ["item"] * (schema.max_items + 1),
                "Boundary",
            ))

        # 3. Unique items enforcement
        if schema.unique_items:
            mutations.append((
                "Integrity: Duplicate Items",
                f"Reject duplicate items in uniqueItems list for '{field_name}'",
                ["duplicate", "duplicate"],
                "Integrity",
            ))

        # 4. Type inversion: Primitive string instead of array
        mutations.append((
            "Type: Scalar String Instead of Array",
            f"Reject single string scalar instead of array for '{field_name}'",
            "not_an_array_string",
            "Type",
        ))

        return mutations
