# SpecForge ⚡

**The Interactive API Client & Automated Contract Testing Engine for Python.**

SpecForge is a modern, drop-in Python library that replaces Swagger UI with a beautiful, responsive API workspace **and** automatically discovers boundary vulnerabilities, missing whitespace stripping, and unhandled 500 server crashes directly against your endpoints.

---

<p align="center">
  <img src="https://raw.githubusercontent.com/specforge-api/specforge/main/docs/images/specforge-preview.png" alt="SpecForge Studio Preview" width="100%" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);" />
</p>

---

## 🚀 Key Advantages

### 1. Active Quality Gate, Not Just Passive Docs
Traditional documentation tools like Swagger UI only show the "happy path" with mock examples. SpecForge algorithmically analyzes your schema constraints and executes targeted boundary fuzzing right in your browser or through the CLI.

### 2. "Zero 500s" Invariant
Verifies that edge-case inputs (e.g. whitespace-only strings `"   "`, empty values, off-by-one numbers, malformed emails) return clean client validation errors (`422/400`), never unhandled server exceptions (`500`).

### 3. One-Click Pytest Exporter
Discovered edge cases and regression vulnerabilities can be instantly exported into commit-ready `test_api_contracts.py` files with standard `@pytest.mark.parametrize` matrices.

### 4. Existing Project Tests Discovery
If your project already has test suites written in `pytest` or `unittest`, SpecForge can automatically index and display them in a dedicated **Project Tests** tab and link them directly to their corresponding API routes.

### 5. Zero Frontend Build Dependencies
The interactive studio is fully compiled and inlined into the Python package. No Node.js, npm, or webpack setup is needed on your machine.

---

## ⚡ Installation in 10 Seconds

```bash
pip install specforge-api
```

With framework extras:

=== "FastAPI"
    ```bash
    pip install "specforge-api[fastapi]"
    ```

=== "Flask"
    ```bash
    pip install "specforge-api[flask]"
    ```

=== "All Frameworks & CLI"
    ```bash
    pip install "specforge-api[all]"
    ```

Ready to explore? Head over to the [Quickstart Guide](quickstart.md) to mount SpecForge in 3 lines of code!
