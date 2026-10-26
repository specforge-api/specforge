# SpecForge ⚡

[![PyPI version](https://img.shields.io/pypi/v/specforge.svg)](https://pypi.org/project/specforge/)
[![Python versions](https://img.shields.io/pypi/pyversions/specforge.svg)](https://pypi.org/project/specforge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**The Interactive API Client & Automated Contract Testing Engine for Python.**

A modern, drop-in Python library that replaces Swagger UI with a beautiful, responsive API workspace **and** automatically discovers boundary vulnerabilities, missing whitespace stripping, and unhandled 500 server crashes directly against your endpoints.

---

## 🚀 Why SpecForge?

1. **Active Quality Gate, Not Just Passive Docs**: Traditional tools like Swagger UI only show the "happy path". SpecForge algorithmically analyzes your schema constraints and runs targeted boundary fuzzing right in your browser.
2. **"Zero 500s" Invariant**: Verifies that edge-case inputs (e.g. `"   "`, empty strings, off-by-one numbers, malformed emails) return clean client errors (`422/400`), never unhandled server exceptions (`500`).
3. **One-Click Pytest Exporter**: Discovered edge cases can be instantly exported into commit-ready `test_api_contracts.py` files with `@pytest.mark.parametrize`.
4. **Zero Frontend Build Dependencies**: The interactive workspace is fully compiled and inlined into the Python package. No Node.js or npm needed on your machine.

---

## 📦 Installation

```bash
pip install specforge
```

With framework extras:
```bash
pip install "specforge[fastapi]"   # FastAPI
pip install "specforge[flask]"     # Flask
pip install "specforge[all]"       # Full CLI & all framework adapters
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

## 🛠️ CLI & CI/CD Pipeline

Run headless contract fuzzing in your continuous integration pipeline:

```bash
specforge test http://localhost:8000/openapi.json --fail-on-500
```

---

## 📄 License

SpecForge is licensed under the [MIT License](LICENSE).
