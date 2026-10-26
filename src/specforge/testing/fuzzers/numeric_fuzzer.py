"""Numeric and integer field boundary test generator."""

from typing import Any, List, Tuple

from specforge.parser.models import JSONSchema


class NumericFuzzer:
    """Generates boundary and mutation payloads for integer and number schema fields."""

    @classmethod
    def generate_mutations(
        cls,
        field_name: str,
        schema: JSONSchema,
        valid_example: float = 10,
    ) -> List[Tuple[str, str, Any, str]]:
        """Generate a list of mutations for a numeric field.

        Returns tuples of: (mutation_name, description, mutated_value, category)
        """
        mutations: List[Tuple[str, str, Any, str]] = []
        is_integer = (
            schema.type == "integer"
            or (isinstance(schema.type, list) and "integer" in schema.type)
        )

        # 1. Minimum boundary
        if schema.minimum is not None:
            subtractor = 1 if is_integer else 0.01
            mutations.append((
                "Boundary: Below Minimum",
                f"Reject value {schema.minimum - subtractor} (< min {schema.minimum}) for '{field_name}'",
                schema.minimum - subtractor,
                "Boundary",
            ))

        # 2. Maximum boundary
        if schema.maximum is not None:
            adder = 1 if is_integer else 0.01
            mutations.append((
                "Boundary: Exceeds Maximum",
                f"Reject value {schema.maximum + adder} (> max {schema.maximum}) for '{field_name}'",
                schema.maximum + adder,
                "Boundary",
            ))

        # 3. Negative value check (if minimum is non-negative)
        if schema.minimum is not None and schema.minimum >= 0:
            mutations.append((
                "Boundary: Negative Number",
                f"Reject negative number (-1) for positive field '{field_name}'",
                -1,
                "Boundary",
            ))

        # 4. Zero check (if minimum is strictly positive)
        if schema.minimum is not None and schema.minimum > 0:
            mutations.append((
                "Boundary: Zero Value",
                f"Reject 0 for field with minimum {schema.minimum} '{field_name}'",
                0,
                "Boundary",
            ))

        # 5. Float into integer field
        if is_integer:
            mutations.append((
                "Type: Float in Integer Field",
                f"Reject non-integer float (42.5) for integer field '{field_name}'",
                42.5,
                "Type",
            ))

        # 6. Integer range overflow
        if is_integer:
            mutations.append((
                "Overflow: 32-bit Integer Limit",
                f"Handle 32-bit integer overflow (2,147,483,648) for '{field_name}'",
                2147483648,
                "Overflow",
            ))

        # 7. Type inversion: String representation of number
        mutations.append((
            "Type: String Instead of Number",
            f"Reject string representation '100' for numeric field '{field_name}'",
            "100",
            "Type",
        ))

        return mutations
