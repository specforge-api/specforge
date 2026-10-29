# FastAPI Integration

SpecForge is designed to be the ultimate companion for **FastAPI**. It seamlessly discovers FastAPI's native `/openapi.json` and injects an interactive workspace without altering your route logic or application state.

---

## Basic Mounting

```python
from fastapi import FastAPI
from specforge import SpecForge

app = FastAPI(title="Payment Gateway API", version="1.0.0")

# Mount SpecForge
SpecForge(app)
```

By default, SpecForge:
- Mounts at `/docs`.
- Automatically fetches `/openapi.json`.
- Disables FastAPI's default Swagger UI so you enjoy the full SpecForge studio.

---

## Customizing Configuration

You can customize the mounting path, spec URL, page title, and existing project tests:

```python
from fastapi import FastAPI
from specforge import SpecForge

app = FastAPI()

SpecForge(
    app,
    path="/api-studio",                  # Custom URL path
    spec_url="/openapi.json",            # Custom spec location
    title="Payment Gateway Studio",      # Browser tab title
    theme="theme-2",                     # Default theme: theme-1 (Indigo), theme-2 (Emerald Teal), theme-3 (Dark), theme-4 (Cobalt)
    test_paths=["tests"],                # Index existing repository tests
    read_only=False,                     # Allow execution of requests and fuzzers
)
```

---

## Security & Production Hardening

In sensitive production environments, you can easily:
- Restrict SpecForge to development environments.
- Protect the documentation and test plan routes with FastAPI dependencies (e.g. API keys or OAuth2):

```python
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from specforge import SpecForge

app = FastAPI()
security = HTTPBasic()

def verify_docs_admin(credentials: HTTPBasicCredentials = Depends(security)):
    expected_user = os.getenv("DOCS_ADMIN_USER", "admin")
    expected_pass = os.getenv("DOCS_ADMIN_PASSWORD")
    if not expected_pass or credentials.username != expected_user or credentials.password != expected_pass:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )

env = os.getenv("ENVIRONMENT", "development")

if env == "development":
    # Mount without authentication in dev
    SpecForge(app)
elif env == "staging":
    # Mount with dependency protection and disabled raw fuzzing endpoints
    SpecForge(
        app,
        dependencies=[Depends(verify_docs_admin)],
        enable_api_endpoints=False,  # Disable /specforge/api/plan and /export-pytest
    )
else:
    # Disable docs entirely in production
    pass
```
