"""Command-line interface for SpecForge."""

import argparse
import ipaddress
import json
import socket
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import httpx

from specforge.parser.openapi3 import OpenAPIParser
from specforge.testing.exporters.pytest_export import PytestExporter
from specforge.testing.invariants import TestStatus, evaluate_test_result
from specforge.testing.planner import TestPlanner

MAX_SPEC_SIZE = 10 * 1024 * 1024  # 10 MB maximum specification size
DEFAULT_FETCH_TIMEOUT = 30.0  # seconds

# Blocked metadata and link-local networks to mitigate cloud metadata SSRF
BLOCKED_IP_NETWORKS = (
    ipaddress.ip_network("169.254.0.0/16"),   # IPv4 Link-local / Cloud metadata (AWS, GCP, Azure, DigitalOcean)
    ipaddress.ip_network("fd00:ec2::/64"),    # AWS IMDSv6
    ipaddress.ip_network("fe80::/10"),        # IPv6 Link-local
    ipaddress.ip_network("224.0.0.0/4"),      # Multicast
    ipaddress.ip_network("ff00::/8"),         # IPv6 Multicast
)


def _validate_spec_url(url: str) -> None:
    """Validate that a URL uses supported schemes and does not target cloud metadata endpoints."""
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {scheme!r}. Only 'http' and 'https' are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"Invalid URL: missing hostname in {url!r}")

    # Check if the hostname itself is an IP or resolves to blocked ranges
    try:
        ip = ipaddress.ip_address(hostname)
        for net in BLOCKED_IP_NETWORKS:
            if ip in net:
                raise ValueError(f"Access to link-local/cloud metadata address {ip} is blocked for security.")
    except ValueError as e:
        if "blocked for security" in str(e):
            raise
        # Hostname is a domain name, attempt address lookup
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for res in addr_info:
                ip = ipaddress.ip_address(res[4][0])
                for net in BLOCKED_IP_NETWORKS:
                    if ip in net:
                        raise ValueError(f"URL resolves to blocked link-local/cloud metadata address: {ip}")
        except socket.gaierror:
            # DNS resolution errors will be raised cleanly by urlopen
            pass


class _RestrictedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Enforces scheme and SSRF validation on redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_spec_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_spec(target: str) -> dict[str, Any]:
    """Load OpenAPI JSON/YAML from a local file or remote HTTP URL."""
    target_lower = target.lower()
    if target_lower.startswith(("http://", "https://")):
        _validate_spec_url(target)
        opener = urllib.request.build_opener(_RestrictedRedirectHandler)
        req = urllib.request.Request(target, headers={"User-Agent": "SpecForge-CLI"})
        with opener.open(req, timeout=DEFAULT_FETCH_TIMEOUT) as response:
            raw_bytes = response.read(MAX_SPEC_SIZE + 1)
            if len(raw_bytes) > MAX_SPEC_SIZE:
                raise ValueError(f"Remote specification exceeds maximum allowed size ({MAX_SPEC_SIZE // (1024 * 1024)} MB).")
            content = raw_bytes.decode("utf-8")
    elif "://" in target:
        scheme = target.split("://", 1)[0]
        raise ValueError(f"Unsupported URL scheme: {scheme!r}. Only 'http' and 'https' are allowed.")
    else:
        # Treat as local filesystem path
        path = Path(target)
        if not path.exists():
            raise FileNotFoundError(f"Spec file not found at: {target}")
        if path.stat().st_size > MAX_SPEC_SIZE:
            raise ValueError(f"Local specification file exceeds maximum allowed size ({MAX_SPEC_SIZE // (1024 * 1024)} MB).")
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
        if out_path.exists() and out_path.is_dir():
            print(f"\n\033[1;31mError: Export path is a directory: {out_path}\033[0m")
            return 1
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
