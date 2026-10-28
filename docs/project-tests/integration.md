# Existing Project Tests Integration

Most production repositories already contain extensive test suites written in `pytest` or `unittest`. SpecForge can automatically index and display these tests in a dedicated **Project Tests** tab and link them directly to their corresponding API routes.

---

## Quick Setup

Pass `test_paths` when mounting SpecForge in your FastAPI or Flask app:

=== "FastAPI"
    ```python
    from fastapi import FastAPI
    from specforge import SpecForge

    app = FastAPI(title="Store API")

    # Pass folder or specific test files
    SpecForge(
        app,
        test_paths=["tests"],
    )
    ```

=== "Flask"
    ```python
    from flask import Flask
    from specforge.flask import SpecForge

    app = Flask(__name__)

    SpecForge(
        app,
        spec_url="/api/spec.json",
        test_paths=["tests"],
    )
    ```

---

## What SpecForge Discovers

When SpecForge mounts, it parses your test files statically (without executing arbitrary test code or fixtures) to extract:
* **Test Functions & Classes**: Names, line numbers, and file paths.
* **Docstrings**: Human-readable descriptions of what each test verifies.
* **Parameterized Matrices**: Extracted `@pytest.mark.parametrize` argument sets.
* **Associated Route Endpoints**: Automatically detected API routes.

---

## How Routes Are Linked

SpecForge links your existing tests to OpenAPI routes using two mechanisms:

### 1. Automatic HTTP Client Detection (Zero Configuration)
If your test uses common test clients (`client.get(...)`, `httpx.post(...)`, `requests.delete(...)`), SpecForge automatically parses the endpoint string and binds the test to that route:

```python
def test_create_user_underage(client):
    """Rejects registration when age is below legal requirement."""
    response = client.post("/users", json={"username": "bob", "age": 12})
    assert response.status_code == 422
```

In the API Explorer, `/users` will now proudly display:
> 🔗 **Associated Project Tests: 1** (`test_create_user_underage`)

### 2. Explicit Annotation Marker
For complex test setups, you can explicitly link a test using a decorator comment or docstring:

```python
def test_complex_billing_workflow(billing_fixture):
    """
    specforge: POST /billing/charge
    Verifies retry logic when third-party gateway responds with timeout.
    """
    ...
```

---

## Security & Isolation

- **Zero Arbitrary Execution**: Tests are discovered via Python's Abstract Syntax Tree (`ast`). SpecForge never runs unvetted test files during discovery.
- **Safe Path Traversal Protection**: SpecForge ensures all scanned files reside strictly within permitted project directories.
