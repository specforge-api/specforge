# Contributing to SpecForge ⚡

Thank you for your interest in contributing to SpecForge! We are building the next generation of interactive API documentation and automated contract testing.

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- Python 3.9+
- Git

### 2. Clone and Setup Environment
```bash
git clone https://github.com/specforge/specforge.git
cd specforge

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install SpecForge in editable mode with all development dependencies
pip install -e ".[all,dev]"
```

---

## 🧪 Running Tests & Quality Checks

Before submitting any code changes, ensure all tests and linting passes:

```bash
# Run unit test suite
pytest

# Run Ruff linter
ruff check .

# Run Mypy static type checker
mypy src/specforge
```

---

## 🧩 Adding a New Fuzzer

All type-specific boundary and mutation fuzzers reside in `src/specforge/testing/fuzzers/`.

1. Implement the fuzzer class adhering to the `generate_mutations` signature:
   ```python
   class CustomFuzzer:
       @classmethod
       def generate_mutations(cls, field_name: str, schema: JSONSchema) -> List[Tuple[str, str, Any, str]]:
           ...
   ```
2. Integrate your fuzzer into `src/specforge/testing/planner.py`.
3. Add unit test coverage in `tests/test_fuzzers.py`.

---

## 🚀 Releasing a New Version

1. Bump the version in `pyproject.toml`.
2. Commit with message: `chore: release vX.Y.Z`.
3. Tag the commit: `git tag vX.Y.Z && git push origin main --tags`.
4. GitHub Actions will automatically run the CI suite and publish to PyPI using Trusted Publishing (OIDC).
