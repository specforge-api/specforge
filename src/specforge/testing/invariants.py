"""Test invariants, status evaluations, and result data structures."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TestStatus(str, Enum):
    PASS = "PASS"                  # Server cleanly rejected invalid input (400/422) or accepted valid input
    WARN_LEAK = "WARN_LEAK"        # Server returned 200 OK for an invalid/boundary payload (Schema Leak)
    CRASH_500 = "CRASH_500"        # Server threw an unhandled 500 error on client input (Critical Crash)
    FAIL_STATUS = "FAIL_STATUS"    # Unexpected status code (e.g. 404 instead of 422)


@dataclass
class TestCase:
    """Represents an executable boundary or negative test case against an API endpoint."""

    id: str
    endpoint: str
    method: str
    field_name: str
    mutation_category: str
    mutation_name: str
    description: str
    payload: Any
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, Any] = field(default_factory=dict)
    expected_status: int = 422
    is_negative_test: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert test case to dictionary for frontend execution or serialization."""
        return {
            "id": self.id,
            "endpoint": self.endpoint,
            "method": self.method,
            "field_name": self.field_name,
            "mutation_category": self.mutation_category,
            "mutation_name": self.mutation_name,
            "description": self.description,
            "payload": self.payload,
            "headers": self.headers,
            "query_params": self.query_params,
            "expected_status": self.expected_status,
            "is_negative_test": self.is_negative_test,
        }


@dataclass
class TestResult:
    """Represents the execution outcome of a TestCase."""

    test_case: TestCase
    actual_status: int
    latency_ms: float
    response_body: str
    status: TestStatus
    message: str
    curl_command: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for frontend inspection."""
        return {
            "test_case": self.test_case.to_dict(),
            "actual_status": self.actual_status,
            "latency_ms": self.latency_ms,
            "response_body": self.response_body,
            "status": self.status.value,
            "message": self.message,
            "curl_command": self.curl_command,
        }


def evaluate_test_result(
    test_case: TestCase,
    status_code: int,
    response_body: str,
    latency_ms: float,
) -> TestResult:
    """Evaluate HTTP execution against contract invariants."""
    curl_cmd = build_curl_command(test_case)

    # Invariant 1: An HTTP 500 on ANY input is an unhandled server crash bug
    if status_code >= 500:
        return TestResult(
            test_case=test_case,
            actual_status=status_code,
            latency_ms=latency_ms,
            response_body=response_body,
            status=TestStatus.CRASH_500,
            message=f"CRITICAL: Server crashed with {status_code} on {test_case.mutation_name}!",
            curl_command=curl_cmd,
        )

    # Invariant 2: Negative test expects a rejection (400 or 422). If 200/201 was returned, it's a schema leak
    if test_case.is_negative_test:
        if 200 <= status_code < 300:
            return TestResult(
                test_case=test_case,
                actual_status=status_code,
                latency_ms=latency_ms,
                response_body=response_body,
                status=TestStatus.WARN_LEAK,
                message=(
                    f"SCHEMA LEAK: Server accepted invalid payload ({test_case.mutation_name}) "
                    f"with HTTP {status_code}. Expected 422 or 400."
                ),
                curl_command=curl_cmd,
            )
        elif status_code in (400, 422):
            return TestResult(
                test_case=test_case,
                actual_status=status_code,
                latency_ms=latency_ms,
                response_body=response_body,
                status=TestStatus.PASS,
                message=f"PASS: Server cleanly rejected {test_case.mutation_name} with HTTP {status_code}.",
                curl_command=curl_cmd,
            )
        else:
            return TestResult(
                test_case=test_case,
                actual_status=status_code,
                latency_ms=latency_ms,
                response_body=response_body,
                status=TestStatus.FAIL_STATUS,
                message=f"UNEXPECTED: Got HTTP {status_code}, expected {test_case.expected_status}.",
                curl_command=curl_cmd,
            )
    else:
        # Happy-path test
        if 200 <= status_code < 300:
            return TestResult(
                test_case=test_case,
                actual_status=status_code,
                latency_ms=latency_ms,
                response_body=response_body,
                status=TestStatus.PASS,
                message=f"PASS: Endpoint succeeded with HTTP {status_code}.",
                curl_command=curl_cmd,
            )
        else:
            return TestResult(
                test_case=test_case,
                actual_status=status_code,
                latency_ms=latency_ms,
                response_body=response_body,
                status=TestStatus.FAIL_STATUS,
                message=f"FAIL: Happy path failed with HTTP {status_code}.",
                curl_command=curl_cmd,
            )


def build_curl_command(test_case: TestCase, base_url: str = "http://localhost:8000") -> str:
    """Generate a clean cURL reproduction command for a test case."""
    import json

    url = f"{base_url.rstrip('/')}{test_case.endpoint}"
    cmd_parts = [f"curl -X {test_case.method.upper()} '{url}'"]

    for h_name, h_val in test_case.headers.items():
        cmd_parts.append(f"-H '{h_name}: {h_val}'")

    if test_case.payload is not None:
        cmd_parts.append("-H 'Content-Type: application/json'")
        payload_str = json.dumps(test_case.payload).replace("'", "'\\''")
        cmd_parts.append(f"-d '{payload_str}'")

    return " \\\n  ".join(cmd_parts)
