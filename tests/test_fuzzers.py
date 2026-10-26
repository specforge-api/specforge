"""Unit tests for type-based boundary fuzzers."""

from specforge.parser.models import JSONSchema
from specforge.testing.fuzzers.array_fuzzer import ArrayFuzzer
from specforge.testing.fuzzers.numeric_fuzzer import NumericFuzzer
from specforge.testing.fuzzers.object_fuzzer import ObjectFuzzer
from specforge.testing.fuzzers.string_fuzzer import StringFuzzer


def test_string_fuzzer_whitespace_and_empty():
    """Verify string fuzzer generates whitespace and boundary length mutations."""
    schema = JSONSchema(
        type="string",
        min_length=3,
        max_length=10,
        format="email",
    )
    mutations = StringFuzzer.generate_mutations("email", schema)
    mutation_names = [m[0] for m in mutations]
    mutated_values = [m[2] for m in mutations]

    # Verify whitespace mutations exist
    assert "Whitespace: Single Space" in mutation_names
    assert "Whitespace: Multi-Space Only" in mutation_names
    assert "     " in mutated_values

    # Verify empty string mutation exists
    assert "Boundary: Empty String" in mutation_names
    assert "" in mutated_values

    # Verify length boundary mutations
    assert "Boundary: Below Min Length" in mutation_names
    assert "Boundary: Exceeds Max Length" in mutation_names
    assert "aa" in mutated_values  # length 2 < min 3
    assert "a" * 11 in mutated_values  # length 11 > max 10

    # Verify format mutations
    assert "Format: Missing At Symbol" in mutation_names
    assert "plainaddress_without_at" in mutated_values

    # Verify emoji and injection mutations
    assert "Unicode: 4-Byte Emojis" in mutation_names
    assert "Security: Basic SQL Injection Probe" in mutation_names


def test_numeric_fuzzer_boundaries_and_coercion():
    """Verify numeric fuzzer generates boundary and type pollution tests."""
    schema = JSONSchema(
        type="integer",
        minimum=1,
        maximum=100,
    )
    mutations = NumericFuzzer.generate_mutations("quantity", schema)
    mutation_names = [m[0] for m in mutations]
    mutated_values = [m[2] for m in mutations]

    # Below minimum (1 - 1 = 0)
    assert "Boundary: Below Minimum" in mutation_names
    assert 0 in mutated_values

    # Exceeds maximum (100 + 1 = 101)
    assert "Boundary: Exceeds Maximum" in mutation_names
    assert 101 in mutated_values

    # Negative number
    assert "Boundary: Negative Number" in mutation_names
    assert -1 in mutated_values

    # Float in integer field
    assert "Type: Float in Integer Field" in mutation_names
    assert 42.5 in mutated_values

    # 32-bit overflow
    assert "Overflow: 32-bit Integer Limit" in mutation_names
    assert 2147483648 in mutated_values


def test_object_fuzzer_required_omissions():
    """Verify object fuzzer produces baseline and combinatorial omission cases."""
    schema = JSONSchema(
        type="object",
        required=["username", "age"],
        properties={
            "username": JSONSchema(type="string"),
            "age": JSONSchema(type="integer", minimum=18),
            "bio": JSONSchema(type="string"),
        },
    )
    baseline = ObjectFuzzer.generate_valid_baseline(schema)
    assert "username" in baseline
    assert "age" in baseline
    assert baseline["age"] == 18

    mutations = ObjectFuzzer.generate_object_mutations(schema, baseline)
    mut_names = [m[0] for m in mutations]
    mut_payloads = [m[2] for m in mutations]

    # Required field omissions
    assert "Structure: Omit Required Field 'username'" in mut_names
    assert "Structure: Omit Required Field 'age'" in mut_names

    # Check payload missing username
    missing_username_payload = next(p for n, _, p, _ in mutations if "username" in n)
    assert "username" not in missing_username_payload
    assert "age" in missing_username_payload

    # Empty payload
    assert "Structure: Empty Object Payload" in mut_names
    assert {} in mut_payloads


def test_array_fuzzer():
    """Verify array fuzzer tests min/max items and uniqueItems."""
    schema = JSONSchema(
        type="array",
        min_items=1,
        max_items=3,
        unique_items=True,
    )
    mutations = ArrayFuzzer.generate_mutations("tags", schema)
    mut_names = [m[0] for m in mutations]
    mut_values = [m[2] for m in mutations]

    assert "Boundary: Empty Array" in mut_names
    assert [] in mut_values

    assert "Boundary: Exceeds Max Items" in mut_names
    assert len(next(v for n, _, v, _ in mutations if "Exceeds" in n)) == 4

    assert "Integrity: Duplicate Items" in mut_names
    assert ["duplicate", "duplicate"] in mut_values
