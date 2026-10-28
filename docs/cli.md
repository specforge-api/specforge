# CLI Reference

SpecForge comes with a built-in Command Line Interface (`specforge`) for working with OpenAPI specifications offline, spinning up mock studios, and running invariant test suites from your terminal.

---

## Installation

The CLI requires the `cli` or `all` extra:

```bash
pip install "specforge-api[all]"
```

Verify installation:
```bash
specforge --help
```

---

## Commands

### `specforge serve`
Launches the standalone interactive studio for any OpenAPI YAML or JSON specification file:

```bash
# Serve local OpenAPI file
specforge serve openapi.yaml --port 8000

# Serve with custom studio title and theme
specforge serve spec.json --title "Customer API" --theme theme-2
```

### `specforge test`
Executes automated boundary and contract tests directly from your terminal against a live running API:

```bash
# Test all endpoints defined in openapi.yaml against target server
specforge test openapi.yaml --base-url http://localhost:8000

# Stop on first 500 error and print reproduction cURL command
specforge test openapi.yaml --base-url http://localhost:8000 --fail-fast
```

### `specforge export`
Exports synthesized boundary test cases for an OpenAPI spec into a pytest test file:

```bash
specforge export openapi.yaml --output tests/test_generated_contracts.py
```

