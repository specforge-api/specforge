"""Zero-dependency standalone demonstration server for SpecForge.

Runs immediately on standard Python (no FastAPI/Uvicorn installation needed).
Serves the SpecForge interactive UI at http://localhost:8000/docs
and implements live endpoints for boundary and contract fuzzing.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
from pathlib import Path

# Configure utf-8 stdout/stderr for Windows console compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from specforge.config import SpecForgeConfig
from specforge.utils.html_injector import render_html

SAMPLE_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "SpecForge Interactive Demo API",
        "version": "1.0.0",
        "description": "Live demonstration API with schema-aware boundary and negative fuzzing."
    },
    "servers": [{"url": "http://localhost:8000"}],
    "paths": {
        "/api/v1/users": {
            "post": {
                "summary": "Create a new user account",
                "description": "Validates username whitespace, age boundaries, and email format.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["username", "email", "age"],
                                "properties": {
                                    "username": {
                                        "type": "string",
                                        "minLength": 3,
                                        "maxLength": 20,
                                        "description": "User login handle"
                                    },
                                    "email": {
                                        "type": "string",
                                        "format": "email",
                                        "description": "Contact email"
                                    },
                                    "age": {
                                        "type": "integer",
                                        "minimum": 18,
                                        "maximum": 120,
                                        "description": "Age in years"
                                    },
                                    "bio": {
                                        "type": "string",
                                        "maxLength": 100,
                                        "description": "Short bio"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "User created successfully"},
                    "422": {"description": "Validation error (rejections for whitespace, empty strings, bounds)"},
                    "500": {"description": "Internal server crash"}
                }
            }
        }
    }
}


class SpecForgeDemoHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the SpecForge standalone server."""

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        if self.path in ("/", "/docs", "/docs/"):
            config = SpecForgeConfig(
                title="SpecForge Quality Studio (Live Demo)",
                spec_url="/openapi.json",
                theme="dark",
                enable_tests=True,
            )
            html = render_html(config, spec_dict=SAMPLE_SPEC)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        elif self.path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(SAMPLE_SPEC).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests (simulating backend contract validations)."""
        if self.path == "/api/v1/users":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)

            try:
                data = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                self._send_json(400, {"detail": "Malformed JSON payload"})
                return

            if not isinstance(data, dict):
                self._send_json(422, {"detail": "Payload must be a JSON object dictionary"})
                return

            # Required fields check
            for req in ["username", "email", "age"]:
                if req not in data:
                    self._send_json(422, {"detail": f"Missing required property: '{req}'"})
                    return

            username = data.get("username")
            age = data.get("age")
            email = data.get("email")

            # 1. Whitespace and empty string check
            if not isinstance(username, str):
                self._send_json(422, {"detail": "'username' must be a string"})
                return
            if username == "" or username.strip() == "":
                self._send_json(422, {"detail": "Validation Error: 'username' cannot be empty or pure whitespace"})
                return
            if len(username) < 3:
                self._send_json(422, {"detail": f"Validation Error: 'username' must be at least 3 chars (got {len(username)})"})
                return

            # 2. Age integer boundary check
            if not isinstance(age, int) or isinstance(age, bool):
                self._send_json(422, {"detail": "'age' must be an integer"})
                return
            if age < 18:
                self._send_json(422, {"detail": f"Validation Error: 'age' must be at least 18 (got {age})"})
                return
            if age > 120:
                self._send_json(422, {"detail": f"Validation Error: 'age' cannot exceed 120 (got {age})"})
                return

            # 3. Email format check
            if "@" not in str(email) or "." not in str(email):
                self._send_json(422, {"detail": "Validation Error: Malformed email address"})
                return

            # Valid response
            self._send_json(200, {
                "status": "success",
                "message": f"User '{username}' registered successfully!",
                "user_id": "usr_99824",
                "username": username,
                "email": email,
                "age": age,
            })
        else:
            self.send_response(404)
            self.end_headers()

    def _send_json(self, status: int, data: dict):
        """Helper to send JSON response with CORS headers."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def main():
    port = 8000
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, SpecForgeDemoHandler)
    print("\n" + "=" * 65)
    print("⚡ \033[1;36mSpecForge Live Interactive Studio & Contract Fuzzer\033[0m")
    print("=" * 65)
    print(f"Server running at: \033[1;32mhttp://localhost:{port}/docs\033[0m")
    print("Press Ctrl+C to stop the server.")
    print("=" * 65 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        httpd.server_close()


if __name__ == "__main__":
    main()
