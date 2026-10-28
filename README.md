# SpecForge ⚡

[![PyPI version](https://img.shields.io/pypi/v/specforge-api)](https://pypi.org/project/specforge-api/)
[![Python versions](https://img.shields.io/pypi/pyversions/specforge-api)](https://pypi.org/project/specforge-api/)
[![CI](https://github.com/specforge-api/specforge/actions/workflows/ci.yml/badge.svg)](https://github.com/specforge-api/specforge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**The Interactive API Client & Automated Contract Testing Engine for Python.**

A modern, drop-in Python library that replaces Swagger UI with a beautiful, responsive API workspace **and** automatically discovers boundary vulnerabilities, missing whitespace stripping, and unhandled 500 server crashes directly against your endpoints.

<p align="center">
  <img src="https://raw.githubusercontent.com/specforge-api/specforge/main/docs/images/specforge-preview.png" alt="SpecForge Interactive Studio & Contract Fuzzer" width="100%" />
</p>

---

## 🚀 Why SpecForge?

1. **Active Quality Gate, Not Just Passive Docs**: Traditional tools like Swagger UI only show the "happy path". SpecForge algorithmically analyzes your schema constraints and runs targeted boundary fuzzing right in your browser.
2. **"Zero 500s" Invariant**: Verifies that edge-case inputs (e.g. `"   "`, empty strings, off-by-one numbers, malformed emails) return clean client errors (`422/400`), never unhandled server exceptions (`500`).
3. **One-Click Pytest Exporter**: Discovered edge cases can be instantly exported into commit-ready `test_api_contracts.py` files with `@pytest.mark.parametrize`.
4. **Zero Frontend Build Dependencies**: The interactive workspace is fully compiled and inlined into the Python package. No Node.js or npm needed on your machine.

---

## 📦 Installation

```bash
pip install specforge-api
```

With framework extras:
```bash
pip install "specforge-api[fastapi]"   # FastAPI
pip install "specforge-api[flask]"     # Flask
pip install "specforge-api[all]"       # Full CLI & all framework adapters
```

---

## ⚡ Quickstart

### FastAPI

```python
from fastapi import FastAPI
from specforge import SpecForge

app = FastAPI(title="My API", version="1.0.0")

# Mount SpecForge (auto-detects /openapi.json)
SpecForge(app)

@app.post("/users")
def create_user(username: str, age: int):
    return {"status": "created", "username": username}
```

Now open `http://localhost:8000/docs` in your browser. You get:
- A modern, interactive dark/light mode API client (Try-It-Out, request history, multi-language code snippets).
- An integrated **Boundary & Contract Testing Tab** to run automated fuzzing on all endpoints with one click.

---

### Flask

```python
from flask import Flask
from specforge.flask import SpecForge

app = Flask(__name__)

# Register Blueprint
SpecForge(app, spec_url="/api/spec.json", path="/docs")
```

---

## 🧪 Schema-Aware Boundary Fuzzing

SpecForge generates targeted test cases according to field types:

| Field Type | Automated Test Coverage |
|---|---|
| **String** | Rejecting whitespace-only (`"   "`), empty strings (`""`), min/max bounds, Unicode 4-byte emojis, null bytes (`\x00`), format violations (email, uuid, datetime), and injection probes. |
| **Number / Integer** | Boundary checks (`min - 1`, `max + 1`), negative values on unsigned fields, zero checks, float-into-integer pollution, and integer overflow. |
| **Boolean** | Strict type testing vs loose coercion (`"true"`, `"yes"`, `1`, `0`, `null`). |
| **Array** | Empty lists (`[]`), `minItems` / `maxItems` boundaries, and `uniqueItems: true` duplicates. |
| **Object** | Combinatorial required field omission, extra unexpected keys (`additionalProperties: false`), and empty bodies. |

---

## 📁 Integrating Existing Project Tests

If your repository already contains test suites (written in `pytest` or `unittest`), SpecForge can automatically index and display them in a dedicated **Project Tests** tab and link them directly to their corresponding API routes.

### Quick Setup

Pass `test_paths` when mounting SpecForge in your application:

```python
from fastapi import FastAPI
from specforge import SpecForge

app = FastAPI()

# Mount SpecForge with existing project tests
SpecForge(
    app,
    test_paths=["tests"],  # Can be directories or individual test files
)
```

Now open `/docs` to see:
- **📁 Project Tests Tab**: Browse all repository tests, file paths, line numbers, docstrings, and parameter matrices.
- **Route Coverage Linking**: View your existing tests directly inside the API Explorer alongside SpecForge's automated boundary fuzzers.

### Linking Tests to API Routes

SpecForge associates existing tests with OpenAPI routes using two mechanisms:

#### 1. Automatic HTTP Client Detection (Zero Configuration)
If your test uses `TestClient`, `httpx`, or `requests` to call an API path, SpecForge automatically recognizes the route:
```python
def test_user_creation_underage(client):
    """Rejects underage registrations."""
    response = client.post("/api/v1/users", json={"username": "bob", "age": 16})
    assert response.status_code == 422
```

#### 2. Explicit Pytest Marker (Recommended for Complex Tests)
For tests with dynamic URLs or mocks, declare the endpoint explicitly:
```python
import pytest

@pytest.mark.endpoint("POST", "/api/v1/users")
def test_user_signup_pipeline():
    """End-to-end user registration and event dispatch."""
    ...
```

### 🔒 Security & Zero-Execution Guarantee

SpecForge uses **Python Static Abstract Syntax Tree (AST) parsing** to discover tests:
- **Zero Code Execution**: SpecForge **never** imports or executes your test files. Tests are analyzed purely as static syntax trees.
- **No Side Effects**: Discovering tests will never trigger database operations, background tasks, or network calls.
- **Path Sandboxing**: Scanned paths are strictly verified to remain within the project root directory, preventing any path traversal.

---

## 🛠️ CLI & CI/CD Pipeline

Run headless contract fuzzing in your continuous integration pipeline:

```bash
specforge test http://localhost:8000/openapi.json --fail-on-500
```

---

## 💻 Local Development & Testing Guide

### 1. Run the Interactive Live Demo (Zero Dependencies)
You can launch and explore SpecForge immediately using Python's standard library:
```bash
python examples/standalone_demo.py
```
Open **`http://localhost:8000/docs`** in your browser to:
- Test API endpoints and inspect formatted JSON responses.
- Click **"⚡ Run Boundary Test Suite"** to watch automated fuzzing of whitespace strings, negative numbers, and missing fields.
- Click **"🐍 Export to Pytest"** to view and copy auto-generated test code.

### 2. Run the Automated Unit Test Suite
```bash
pytest -v
```

### 3. Install in Another Project Locally (Editable Mode)
To use this local version inside any other Python app on your machine without publishing to PyPI:
```bash
# In your other project's directory and virtualenv:
pip install -e c:\Research-projects\specforge
```
*Any change you make in SpecForge source code will instantly reflect in your other application without reinstalling!*

### 4. Build a Distribution Wheel (.whl)
```bash
pip install build
python -m build
# Outputs wheel file in dist/specforge-0.1.0-py3-none-any.whl
```

---

## 📄 License

SpecForge is licensed under the [MIT License](LICENSE).
