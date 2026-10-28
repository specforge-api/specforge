# Flask Integration

SpecForge integrates with **Flask** as a standard `Blueprint`, giving you the complete interactive API client, fuzzing engine, and existing test explorer.

---

## Basic Mounting

```python
from flask import Flask, jsonify
from specforge.flask import SpecForge

app = Flask(__name__)

# Register SpecForge Blueprint
SpecForge(
    app,
    spec_url="/api/spec.json",    # Path to your OpenAPI JSON route
    path="/docs",                 # URL where SpecForge will be served
)

@app.route("/api/spec.json")
def get_spec():
    # Return your OpenAPI 3.0+ schema dictionary or loaded YAML
    return jsonify({
        "openapi": "3.0.0",
        "info": {"title": "Flask API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)
```

---

## Configuration Options

When mounting on a Flask application:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `app` | `Flask` | *Required* | Your Flask application instance. |
| `spec_url` | `str` | `"/openapi.json"` | Route where your OpenAPI JSON/YAML is accessible. |
| `path` | `str` | `"/docs"` | Route where the SpecForge studio HTML is mounted. |
| `title` | `str` | `"SpecForge - API Explorer & Quality Gate"` | HTML page title. |
| `theme` | `str` | `"theme-1"` | Initial UI color theme (`theme-1`, `theme-2`, `theme-3`, `theme-4`). |
| `test_paths` | `list[str]` | `None` | Directories or files to discover existing pytest/unittest suites. |

