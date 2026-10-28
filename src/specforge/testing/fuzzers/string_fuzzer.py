"""String field boundary and negative test generator."""

from typing import Any

from specforge.parser.models import JSONSchema


class StringFuzzer:
    """Generates boundary and mutation payloads for string schema fields."""

    @classmethod
    def generate_mutations(
        cls,
        field_name: str,
        schema: JSONSchema,
        valid_example: str = "valid_sample",
    ) -> list[tuple[str, str, Any, str]]:
        """Generate a list of mutations for a string field.

        Returns tuples of: (mutation_name, description, mutated_value, category)
        """
        mutations: list[tuple[str, str, Any, str]] = []

        # 1. Whitespace Fuzzing
        mutations.append((
            "Whitespace: Single Space",
            f"Reject single space string for '{field_name}'",
            " ",
            "Whitespace",
        ))
        mutations.append((
            "Whitespace: Multi-Space Only",
            f"Reject multiple whitespace-only string for '{field_name}'",
            "     ",
            "Whitespace",
        ))
        mutations.append((
            "Whitespace: Tabs and Newlines",
            f"Reject tab and newline whitespace for '{field_name}'",
            "\t\n\r  ",
            "Whitespace",
        ))

        # 2. Empty String
        if schema.min_length is None or schema.min_length > 0:
            mutations.append((
                "Boundary: Empty String",
                f"Reject empty string for '{field_name}'",
                "",
                "Boundary",
            ))

        # 3. Min/Max Length Boundaries
        if schema.min_length is not None and schema.min_length > 1:
            mutations.append((
                "Boundary: Below Min Length",
                f"Reject string of length {schema.min_length - 1} (< min {schema.min_length}) for '{field_name}'",
                "a" * (schema.min_length - 1),
                "Boundary",
            ))

        if schema.max_length is not None:
            mutations.append((
                "Boundary: Exceeds Max Length",
                f"Reject string of length {schema.max_length + 1} (> max {schema.max_length}) for '{field_name}'",
                "a" * (schema.max_length + 1),
                "Boundary",
            ))
        else:
            # Test buffer DoS guardrails
            mutations.append((
                "Buffer: Large String (5000 chars)",
                f"Safely handle 5,000-character payload for '{field_name}'",
                "x" * 5000,
                "Buffer",
            ))

        # 4. Unicode & Special Characters
        mutations.append((
            "Unicode: 4-Byte Emojis",
            f"Verify 4-byte UTF-8 emoji support (no crash) for '{field_name}'",
            "🚀✨🔥💡",
            "Unicode",
        ))
        mutations.append((
            "Unicode: Null Byte Injection",
            f"Reject or escape null byte injection in '{field_name}'",
            "admin\x00root",
            "Security",
        ))

        # 5. Format-Specific Fuzzing
        if schema.format == "email":
            mutations.append((
                "Format: Missing At Symbol",
                f"Reject malformed email without '@' in '{field_name}'",
                "plainaddress_without_at",
                "Format",
            ))
            mutations.append((
                "Format: Missing Domain",
                f"Reject incomplete email '@domain.com' in '{field_name}'",
                "@domain.com",
                "Format",
            ))
        elif schema.format == "uuid":
            mutations.append((
                "Format: Malformed UUID",
                f"Reject invalid UUID string in '{field_name}'",
                "not-a-valid-uuid-12345",
                "Format",
            ))
        elif schema.format in ("date-time", "date"):
            mutations.append((
                "Format: Impossible Date",
                f"Reject invalid date (Feb 31st) in '{field_name}'",
                "2026-02-31T00:00:00Z",
                "Format",
            ))
            mutations.append((
                "Format: Non-ISO Date String",
                f"Reject non-ISO date string in '{field_name}'",
                "Tomorrow morning",
                "Format",
            ))
        elif schema.format == "uri":
            mutations.append((
                "Format: Missing URI Protocol",
                f"Reject URI missing scheme (http/https) in '{field_name}'",
                "www.example.com/no-protocol",
                "Format",
            ))

        # 6. Injection Probes (Safety heuristics)
        mutations.append((
            "Security: Basic SQL Injection Probe",
            f"Safely validate/escape SQL injection probe in '{field_name}'",
            "' OR '1'='1",
            "Security",
        ))
        mutations.append((
            "Security: XSS Script Tag Probe",
            f"Safely validate/escape script tag in '{field_name}'",
            "<script>alert(1)</script>",
            "Security",
        ))

        # 7. Pattern Non-Compliance
        if schema.pattern:
            mutations.append((
                "Pattern: Non-Matching String",
                f"Reject string violating pattern '{schema.pattern}' for '{field_name}'",
                "__INVALID_PATTERN_VIOLATION__!",
                "Pattern",
            ))

        return mutations
