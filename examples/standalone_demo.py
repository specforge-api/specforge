"""Zero-dependency standalone demonstration server for SpecForge.

Runs immediately on standard Python (no FastAPI/Uvicorn installation needed).
Serves the SpecForge interactive UI at http://localhost:8000/docs
and implements live endpoints for testing headers, query parameters, path variables, and body fuzzing.
"""

import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
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
        "description": "Live demonstration API with Query Params, Path Variables, Custom Headers, and Body Fuzzing."
    },
    "servers": [{"url": "http://localhost:8000"}],
    "paths": {
        "/api/v1/users": {
            "get": {
                "summary": "List users with filtering & pagination",
                "description": "Demonstrates Query Parameters (limit, role, search)",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "description": "Max users to return (1-100)",
                        "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10},
                        "example": 10
                    },
                    {
                        "name": "role",
                        "in": "query",
                        "required": False,
                        "description": "Filter by user role",
                        "schema": {"type": "string", "enum": ["admin", "editor", "viewer"], "default": "editor"},
                        "example": "editor"
                    },
                    {
                        "name": "search",
                        "in": "query",
                        "required": False,
                        "description": "Search keyword (cannot be whitespace only)",
                        "schema": {"type": "string"},
                        "example": "alice"
                    }
                ],
                "responses": {
                    "200": {"description": "List of users matching filter"},
                    "422": {"description": "Query parameter validation error"}
                }
            },
            "post": {
                "summary": "Create a new user account",
                "description": "Validates username whitespace, age boundaries, email format, and optional custom header.",
                "parameters": [
                    {
                        "name": "X-Client-Trace",
                        "in": "header",
                        "required": False,
                        "description": "Client-side telemetry trace ID",
                        "schema": {"type": "string"},
                        "example": "trace_99214_alpha"
                    }
                ],
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
        },
        "/api/v1/users/{user_id}": {
            "get": {
                "summary": "Retrieve user by ID",
                "description": "Demonstrates Path Variables ({user_id})",
                "parameters": [
                    {
                        "name": "user_id",
                        "in": "path",
                        "required": True,
                        "description": "Unique user identifier",
                        "schema": {"type": "string", "minLength": 3},
                        "example": "usr_99824"
                    }
                ],
                "responses": {
                    "200": {"description": "User details"},
                    "404": {"description": "User not found"},
                    "422": {"description": "Malformed user_id path parameter"}
                }
            },
            "delete": {
                "summary": "Delete user by ID (Authenticated)",
                "description": "Demonstrates Path Variables + Bearer Token Authorization Header",
                "parameters": [
                    {
                        "name": "user_id",
                        "in": "path",
                        "required": True,
                        "description": "Unique user identifier to delete",
                        "schema": {"type": "string"},
                        "example": "usr_99824"
                    },
                    {
                        "name": "Authorization",
                        "in": "header",
                        "required": True,
                        "description": "Bearer token authentication (e.g. Bearer my_secret_token)",
                        "schema": {"type": "string"},
                        "example": "Bearer my_secret_token_123"
                    }
                ],
                "responses": {
                    "200": {"description": "User deleted successfully"},
                    "401": {"description": "Unauthorized: Missing or invalid Bearer token"}
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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Client-Trace, X-API-Key")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ("/", "/docs", "/docs/"):
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

        elif path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(SAMPLE_SPEC).encode("utf-8"))

        elif path == "/api/v1/users":
            # Query parameters testing
            limit_raw = query.get("limit", ["10"])[0]
            role = query.get("role", ["editor"])[0]
            search = query.get("search", [""])[0]

            # 1. Test numeric boundary on limit query param
            try:
                limit = int(limit_raw)
            except ValueError:
                self._send_json(422, {"detail": "Query param 'limit' must be an integer"})
                return

            if limit < 1:
                self._send_json(422, {"detail": f"Query param 'limit' must be >= 1 (got {limit})"})
                return
            if limit > 100:
                self._send_json(422, {"detail": f"Query param 'limit' cannot exceed 100 (got {limit})"})
                return

            # 2. Test whitespace on search query param
            if search != "" and search.strip() == "":
                self._send_json(422, {"detail": "Query param 'search' cannot be composed entirely of whitespace"})
                return

            # Return user list
            mock_users = [
                {"user_id": f"usr_{100 + i}", "username": f"user_{role}_{i}", "role": role, "email": f"user{i}@example.com"}
                for i in range(min(limit, 5))
            ]
            self._send_json(200, {
                "total": len(mock_users),
                "limit": limit,
                "role_filter": role,
                "search_query": search or None,
                "users": mock_users
            })

        elif path.startswith("/api/v1/users/"):
            # Path parameter testing
            user_id = path.split("/api/v1/users/")[1]

            if not user_id or user_id.strip() == "":
                self._send_json(422, {"detail": "Path parameter 'user_id' cannot be empty or whitespace"})
                return
            if len(user_id) < 3:
                self._send_json(422, {"detail": f"Path parameter 'user_id' must be at least 3 chars (got '{user_id}')"})
                return

            if user_id == "404" or user_id == "not_found":
                self._send_json(404, {"detail": f"User '{user_id}' does not exist"})
                return

            self._send_json(200, {
                "user_id": user_id,
                "username": f"alice_{user_id}",
                "email": f"{user_id}@example.com",
                "role": "admin",
                "status": "active"
            })

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests (simulating backend contract validations)."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/v1/users":
            trace_header = self.headers.get("X-Client-Trace", "none")
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
                "trace_id": trace_header
            })
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        """Handle DELETE requests (testing path variables + authentication headers)."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/v1/users/"):
            user_id = path.split("/api/v1/users/")[1]
            auth_header = self.headers.get("Authorization", "")

            # Verify Bearer Token in Authorization header
            if not auth_header or not auth_header.startswith("Bearer "):
                self._send_json(401, {
                    "detail": "Unauthorized: Missing or malformed 'Authorization' header. Expected 'Bearer <token>'."
                })
                return

            token = auth_header.split("Bearer ", 1)[1].strip()
            if not token:
                self._send_json(401, {"detail": "Unauthorized: Empty Bearer token provided."})
                return

            self._send_json(200, {
                "status": "deleted",
                "message": f"User '{user_id}' has been permanently deleted.",
                "user_id": user_id,
                "authorized_by_token": token[:6] + "..."
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
        self.send_header("X-SpecForge-Latency", "0.2ms")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))


def main():
    port = 8000
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, SpecForgeDemoHandler)
    print("\n" + "=" * 65)
    print("SpecForge Live Interactive Studio & Contract Fuzzer")
    print("=" * 65)
    print(f"Server running at: http://localhost:{port}/docs")
    print("Supports: Query Params, Path Variables, Custom Headers, and Body Fuzzing")
    print("Press Ctrl+C to stop the server.")
    print("=" * 65 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        httpd.server_close()


if __name__ == "__main__":
    main()
