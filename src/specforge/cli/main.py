"""Command-line interface for SpecForge."""

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import httpx

from specforge.parser.openapi3 import OpenAPIParser
from specforge.testing.exporters.pytest_export import PytestExporter
from specforge.testing.invariants import TestStatus, evaluate_test_result
from specforge.testing.planner import TestPlanner


def fetch_spec(target: str) -> dict[str, Any]:
    """Load OpenAPI JSON/YAML from a local file or remote HTTP URL."""
    if target.startswith("http://") or target.startswith("https://"):
        req = urllib.request.Request(target, headers={"User-Agent": "SpecForge-CLI"})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode("utf-8")
    else:
        path = Path(target)
        if not path.exists():
            raise FileNotFoundError(f"Spec file not found at: {target}")
        content = path.read_text(encoding="utf-8")

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        import yaml  # type: ignore
        return yaml.safe_load(content)


def run_test_command(args: argparse.Namespace) -> int:
    """Execute automated contract fuzzing against an API from the terminal."""
    print("\n⚡ \033[1;36mSpecForge Contract & Boundary Testing Engine\033[0m")
    print(f"Loading specification from: \033[33m{args.spec}\033[0m")

    try:
        raw_spec = fetch_spec(args.spec)
    except Exception as e:
        print(f"\033[1;31mError loading spec: {e}\033[0m")
        return 1

    parser = OpenAPIParser(raw_spec)
    spec_model = parser.parse()
    print(f"Parsed \033[32m{len(spec_model.operations)}\033[0m operations across API: {spec_model.title}\n")

    all_test_cases = []
    for op in spec_model.operations:
        plan = TestPlanner.plan_operation_tests(op)
        all_test_cases.extend(plan.test_cases)

    print(f"Synthesized \033[1;35m{len(all_test_cases)}\033[0m boundary test cases.\n")
    print("=" * 80)

    base_url = args.base_url or (spec_model.servers[0] if spec_model.servers else "http://localhost:8000")
    base_url = base_url.rstrip("/")

    pass_count = 0
    leak_count = 0
    crash_count = 0
    fail_count = 0

    with httpx.Client(base_url=base_url, timeout=args.timeout) as client:
        for _idx, tc in enumerate(all_test_cases, 1):
            start = time.perf_counter()
            kwargs: dict[str, Any] = {}
            if tc.payload is not None:
                kwargs["json"] = tc.payload
            if tc.query_params:
                kwargs["params"] = tc.query_params

            try:
                res = client.request(tc.method.upper(), tc.endpoint, **kwargs)
                actual_status = res.status_code
                resp_text = res.text
            except Exception as e:
                actual_status = 599
                resp_text = str(e)

            latency = (time.perf_counter() - start) * 1000
            result = evaluate_test_result(tc, actual_status, resp_text, latency)

            if result.status == TestStatus.PASS:
                pass_count += 1
                status_icon = "\033[32m[PASS]\033[0m"
            elif result.status == TestStatus.CRASH_500:
                crash_count += 1
                status_icon = "\033[1;31m[CRASH 500]\033[0m"
            elif result.status == TestStatus.WARN_LEAK:
                leak_count += 1
                status_icon = "\033[33m[LEAK 200]\033[0m"
            else:
                fail_count += 1
                status_icon = f"\033[31m[{actual_status}]\033[0m"

            print(
                f"{status_icon} {tc.method.upper():<6} {tc.endpoint:<28} "
                f"Field: {tc.field_name:<16} ({latency:4.0f}ms)"
            )
            if result.status == TestStatus.CRASH_500:
                print(f"       \033[31m↳ {result.message}\033[0m")
                print(f"       \033[90mReproduction:\033[0m {result.curl_command}")

    print("=" * 80)
    print("\n📊 \033[1mFinal Test Summary:\033[0m")
    print(f"   Total Executed: {len(all_test_cases)}")
    print(f"   \033[32mPassed (Clean 400/422):  {pass_count}\033[0m")
    print(f"   \033[33mSchema Leaks (Accepted): {leak_count}\033[0m")
    print(f"   \033[1;31mServer Crashes (500s):  {crash_count}\033[0m")

    # Export to pytest if requested
    if args.export_pytest:
        out_path = Path(args.export_pytest)
        code = PytestExporter.export(all_test_cases, base_url=base_url)
        out_path.write_text(code, encoding="utf-8")
        print(f"\n🐍 \033[32mExported Pytest suite to: {out_path.resolve()}\033[0m")

    if args.fail_on_500 and crash_count > 0:
        print(f"\n\033[1;31mFAILED: {crash_count} unhandled HTTP 500 server crashes detected!\033[0m")
        return 1

    return 0


def cli_entrypoint() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="specforge",
        description="SpecForge: Interactive API Client & Automated Contract Fuzzer",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # `specforge test` command
    test_parser = subparsers.add_parser("test", help="Run automated boundary tests against an API")
    test_parser.add_argument("spec", help="Path or URL to OpenAPI JSON/YAML spec")
    test_parser.add_argument("--base-url", help="Target API base URL (e.g. http://localhost:8000)")
    test_parser.add_argument("--timeout", type=float, default=10.0, help="HTTP request timeout in seconds")
    test_parser.add_argument("--fail-on-500", action="store_true", default=True, help="Exit with code 1 on HTTP 500 crashes")
    test_parser.add_argument("--export-pytest", help="File path to save generated pytest test suite")

    args = parser.parse_args()
    if args.command == "test":
        sys.exit(run_test_command(args))


if __name__ == "__main__":
    cli_entrypoint()
