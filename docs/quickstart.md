# Quickstart Guide

Get up and running with SpecForge in less than a minute.

---

## 1. Installation

Install SpecForge from PyPI:

```bash
pip install "specforge-api[all]"
```

---

## 2. Mount SpecForge in Your Application

=== "FastAPI"
    ```python
    from fastapi import FastAPI
    from specforge import SpecForge

    app = FastAPI(title="Store API", version="1.0.0")

    # Mount SpecForge (automatically replaces /docs and auto-detects /openapi.json)
    SpecForge(app)

    @app.post("/items")
    def create_item(name: str, price: float):
        return {"name": name, "price": price}
    ```

    Run your app:
    ```bash
    uvicorn main:app --reload
    ```
    Open `http://localhost:8000/docs` in your browser.

=== "Flask"
    ```python
    from flask import Flask
    from specforge.flask import SpecForge

    app = Flask(__name__)

    # Mount SpecForge pointing to your OpenAPI JSON spec
    SpecForge(app, spec_url="/api/spec.json", path="/docs")

    if __name__ == "__main__":
        app.run(port=5000, debug=True)
    ```

    Open `http://localhost:5000/docs` in your browser.

---

## 3. What You Get at `/docs`

Once you open the docs endpoint:

1. **Interactive API Explorer**:
   - Send requests with live header, query, and JSON body editors.
   - Inspect response statuses, timing, headers, and formatted bodies.
   - One-click cURL, Python (`httpx`), and JavaScript (`fetch`) snippet generators.

2. **Automated Schema Boundary Fuzzing**:
   - Switch to the **Automated Tests** section on any route.
   - Run combinatorial boundary attacks against string lengths, numerical constraints, required fields, and formatting rules.
   - Instantly uncover whether your API handles bad inputs cleanly or crashes with `500 Internal Server Error`.

3. **Export to Pytest**:
   - Click **Export Pytest** to download a production-ready test file parametrized with every generated edge case.

