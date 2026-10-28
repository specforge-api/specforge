"""Test Plan orchestrator that assembles boundary test suites for operations."""

import copy
import uuid
from dataclasses import dataclass, field
from typing import Any

from specforge.parser.models import Operation
from specforge.testing.fuzzers.array_fuzzer import ArrayFuzzer
from specforge.testing.fuzzers.boolean_fuzzer import BooleanFuzzer
from specforge.testing.fuzzers.numeric_fuzzer import NumericFuzzer
from specforge.testing.fuzzers.object_fuzzer import ObjectFuzzer
from specforge.testing.fuzzers.string_fuzzer import StringFuzzer
from specforge.testing.invariants import TestCase


@dataclass
class TestPlan:
    """Represents the complete test suite planned for an operation or API."""

    operation_key: str
    endpoint: str
    method: str
    test_cases: list[TestCase] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert test plan to dictionary."""
        return {
            "operation_key": self.operation_key,
            "endpoint": self.endpoint,
            "method": self.method,
            "total_tests": len(self.test_cases),
            "test_cases": [tc.to_dict() for tc in self.test_cases],
        }


class TestPlanner:
    """Assembles combinatorial test cases by coordinating type fuzzers."""

    @classmethod
    def plan_operation_tests(cls, operation: Operation) -> TestPlan:
        """Construct full boundary and negative test suite for a single operation."""
        test_cases: list[TestCase] = []
        op_key = operation.key
        endpoint = operation.path
        method = operation.method.lower()

        # 1. Request Body Fuzzing
        if operation.request_body and operation.request_body.schema:
            body_schema = operation.request_body.schema
            baseline = ObjectFuzzer.generate_valid_baseline(body_schema)

            # Test 1.0: Baseline Happy Path
            test_cases.append(
                TestCase(
                    id=str(uuid.uuid4())[:8],
                    endpoint=endpoint,
                    method=method,
                    field_name="[body_root]",
                    mutation_category="Baseline",
                    mutation_name="Happy Path: Valid Schema Payload",
                    description="Verify endpoint succeeds with schema-compliant baseline data",
                    payload=baseline,
                    expected_status=200,
                    is_negative_test=False,
                )
            )

            # Test 1.1: Object-level mutations (missing keys, extra keys, primitive inversion)
            object_mutations = ObjectFuzzer.generate_object_mutations(body_schema, baseline)
            for mut_name, mut_desc, mut_payload, mut_cat in object_mutations:
                test_cases.append(
                    TestCase(
                        id=str(uuid.uuid4())[:8],
                        endpoint=endpoint,
                        method=method,
                        field_name="[body_root]",
                        mutation_category=f"Object:{mut_cat}",
                        mutation_name=mut_name,
                        description=mut_desc,
                        payload=mut_payload,
                        expected_status=422,
                        is_negative_test=True,
                    )
                )

            # Test 1.2: Field-level property mutations
            for prop_name, prop_schema in body_schema.properties.items():
                field_mutations = []
                schema_type = prop_schema.type

                if schema_type == "string":
                    field_mutations = StringFuzzer.generate_mutations(prop_name, prop_schema)
                elif schema_type in ("integer", "number"):
                    field_mutations = NumericFuzzer.generate_mutations(prop_name, prop_schema)
                elif schema_type == "boolean":
                    field_mutations = BooleanFuzzer.generate_mutations(prop_name, prop_schema)
                elif schema_type == "array":
                    field_mutations = ArrayFuzzer.generate_mutations(prop_name, prop_schema)

                # Inject each mutated field value into a fresh copy of the baseline payload
                for mut_name, mut_desc, mut_val, mut_cat in field_mutations:
                    mutated_payload = copy.deepcopy(baseline)
                    mutated_payload[prop_name] = mut_val

                    test_cases.append(
                        TestCase(
                            id=str(uuid.uuid4())[:8],
                            endpoint=endpoint,
                            method=method,
                            field_name=prop_name,
                            mutation_category=f"{str(schema_type or 'field').capitalize()}:{mut_cat}",
                            mutation_name=mut_name,
                            description=mut_desc,
                            payload=mutated_payload,
                            expected_status=422,
                            is_negative_test=True,
                        )
                    )

        # 2. Query Parameter Fuzzing
        for param in operation.parameters:
            if param.location.value == "query" and param.schema:
                param_name = param.name
                param_type = param.schema.type

                param_mutations = []
                if param_type == "string":
                    param_mutations = StringFuzzer.generate_mutations(param_name, param.schema)
                elif param_type in ("integer", "number"):
                    param_mutations = NumericFuzzer.generate_mutations(param_name, param.schema)

                for mut_name, mut_desc, mut_val, mut_cat in param_mutations:
                    test_cases.append(
                        TestCase(
                            id=str(uuid.uuid4())[:8],
                            endpoint=endpoint,
                            method=method,
                            field_name=param_name,
                            mutation_category=f"QueryParam:{mut_cat}",
                            mutation_name=mut_name,
                            description=mut_desc,
                            payload=None,
                            query_params={param_name: mut_val},
                            expected_status=422,
                            is_negative_test=True,
                        )
                    )

        return TestPlan(
            operation_key=op_key,
            endpoint=endpoint,
            method=method,
            test_cases=test_cases,
        )
