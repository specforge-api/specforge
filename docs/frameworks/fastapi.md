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
- Protect the `/docs` route with FastAPI dependencies (e.g. API keys or OAuth2):

```python
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from specforge import SpecForge

app = FastAPI()
security = HTTPBasic()

def verify_docs_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "admin" or credentials.password != "secret":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

if os.getenv("ENVIRONMENT") == "development":
    # Mount without auth in dev
    SpecForge(app)
else:
    # Mount with dependency protection in staging/prod
    # (Or omit to disable docs entirely in production)
    SpecForge(app)
```

