"""Unit tests for TestPlanner and PytestExporter."""

from specforge.parser.models import JSONSchema, Operation, RequestBody
from specforge.testing.exporters.pytest_export import PytestExporter
from specforge.testing.planner import TestPlanner


def test_test_planner_synthesizes_cases():
    """Verify TestPlanner synthesizes baseline and mutation test cases for an operation."""
    body_schema = JSONSchema(
        type="object",
        required=["username", "age"],
        properties={
            "username": JSONSchema(type="string", min_length=3),
            "age": JSONSchema(type="integer", minimum=18),
        },
    )
    operation = Operation(
        method="post",
        path="/api/v1/users",
        request_body=RequestBody(
            required=True,
            content_type="application/json",
            schema=body_schema,
        ),
    )

    plan = TestPlanner.plan_operation_tests(operation)
    assert plan.endpoint == "/api/v1/users"
    assert plan.method == "post"
    assert len(plan.test_cases) > 5

    # Check baseline happy path test exists
    happy_path = next(tc for tc in plan.test_cases if not tc.is_negative_test)
    assert happy_path.expected_status == 200
    assert happy_path.payload["username"] == "sample_username"

    # Check whitespace string mutation exists
    whitespace_test = next(
        tc for tc in plan.test_cases
        if tc.mutation_name == "Whitespace: Multi-Space Only"
    )
    assert whitespace_test.field_name == "username"
    assert whitespace_test.payload["username"] == "     "
    assert whitespace_test.expected_status == 422

    # Check numeric below-min mutation exists
    numeric_test = next(
        tc for tc in plan.test_cases
        if tc.mutation_name == "Boundary: Below Minimum"
    )
    assert numeric_test.field_name == "age"
    assert numeric_test.payload["age"] == 17
    assert numeric_test.expected_status == 422


def test_pytest_exporter_generates_valid_code():
    """Verify PytestExporter generates valid Python pytest code with invariants."""
    body_schema = JSONSchema(
        type="object",
        required=["username"],
        properties={
            "username": JSONSchema(type="string"),
        },
    )
    operation = Operation(
        method="post",
        path="/users",
        request_body=RequestBody(schema=body_schema),
    )
    plan = TestPlanner.plan_operation_tests(operation)

    code = PytestExporter.export(plan.test_cases, base_url="http://testserver")

    # Assert essential structural components in generated Python code
    assert "import pytest" in code
    assert "import httpx" in code
    assert '@pytest.mark.parametrize' in code
    assert 'assert response.status_code != 500' in code
    assert 'assert response.status_code in (400, 422)' in code

    # Verify that the generated code is syntactically valid Python
    compile(code, "<string>", "exec")


def test_query_param_numeric_uses_non_numeric_string():
    """Verify numeric query parameters test non-numeric strings instead of valid numeric strings."""
    from specforge.parser.models import Parameter, ParameterLocation

    operation = Operation(
        method="get",
        path="/items",
        parameters=[
            Parameter(
                name="limit",
                location=ParameterLocation.QUERY,
                required=False,
                schema=JSONSchema(type="integer", minimum=1, maximum=100),
            )
        ],
    )
    plan = TestPlanner.plan_operation_tests(operation)
    values = [tc.query_params.get("limit") for tc in plan.test_cases if tc.field_name == "limit"]
    assert "not_a_number" in values
    assert "100" not in values


def test_resilience_probes_allow_accepted_unless_500():
    """Verify resilience probes pass on 2xx/4xx and still fail on 500."""
    from specforge.testing.invariants import TestStatus, evaluate_test_result

    body_schema = JSONSchema(
        type="object",
        required=["name"],
        properties={"name": JSONSchema(type="string")},
    )
    operation = Operation(
        method="post",
        path="/items",
        request_body=RequestBody(schema=body_schema),
    )
    plan = TestPlanner.plan_operation_tests(operation)
    emoji_tc = next(tc for tc in plan.test_cases if tc.mutation_name == "Unicode: 4-Byte Emojis")
    assert emoji_tc.allow_accepted is True
    assert evaluate_test_result(emoji_tc, 200, "{}", 1.0).status == TestStatus.PASS
    assert evaluate_test_result(emoji_tc, 422, "{}", 1.0).status == TestStatus.PASS
    assert evaluate_test_result(emoji_tc, 500, "err", 1.0).status == TestStatus.CRASH_500
