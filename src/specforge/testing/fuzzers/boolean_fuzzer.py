"""Boolean field mutation test generator."""

from typing import Any, List, Tuple

from specforge.parser.models import JSONSchema


class BooleanFuzzer:
    """Generates boundary and mutation payloads for boolean schema fields."""

    @classmethod
    def generate_mutations(
        cls,
        field_name: str,
        schema: JSONSchema,
        valid_example: bool = True,
    ) -> List[Tuple[str, str, Any, str]]:
        """Generate mutations for boolean field."""
        return [
            (
                "Type: String 'yes' for Boolean",
                f"Reject ambiguous string 'yes' for boolean field '{field_name}'",
                "yes",
                "Type",
            ),
            (
                "Type: Numeric 1 for Boolean",
                f"Reject numeric integer 1 for strict boolean field '{field_name}'",
                1,
                "Type",
            ),
            (
                "Type: Invalid String for Boolean",
                f"Reject arbitrary string 'not_a_bool' for boolean '{field_name}'",
                "not_a_bool",
                "Type",
            ),
        ]
