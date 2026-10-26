"""Unit tests for OpenAPI 3.x parser and reference resolver."""

import pytest
from specforge.parser.openapi3 import OpenAPIParser
from specforge.parser.resolver import RefResolver


SAMPLE_OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "Payment API",
        "version": "1.0.0",
        "description": "Payment microservice"
    },
    "servers": [{"url": "http://localhost:8000"}],
    "paths": {
        "/api/v1/payments": {
            "post": {
                "summary": "Process payment transaction",
                "operationId": "create_payment",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/PaymentRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Payment successful",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "transaction_id": {"type": "string", "format": "uuid"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "PaymentRequest": {
                "type": "object",
                "required": ["amount", "currency", "customer_email"],
                "properties": {
                    "amount": {
                        "type": "number",
                        "minimum": 0.01,
                        "maximum": 10000.0
                    },
                    "currency": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 3
                    },
                    "customer_email": {
                        "type": "string",
                        "format": "email"
                    },
                    "description": {
                        "type": "string"
                    }
                }
            }
        }
    }
}


def test_ref_resolver():
    """Verify $ref pointers are correctly dereferenced."""
    resolver = RefResolver(SAMPLE_OPENAPI_SPEC)
    resolved = resolver.resolve_pointer("#/components/schemas/PaymentRequest")
    assert resolved["type"] == "object"
    assert "amount" in resolved["properties"]
    assert resolved["required"] == ["amount", "currency", "customer_email"]


def test_circular_ref_protection():
    """Verify cyclic schemas do not trigger infinite recursion."""
    cyclic_spec = {
        "components": {
            "schemas": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "parent": {"$ref": "#/components/schemas/Node"}
                    }
                }
            }
        }
    }
    resolver = RefResolver(cyclic_spec)
    dereferenced = resolver.dereference(cyclic_spec["components"]["schemas"]["Node"])
    assert dereferenced["type"] == "object"
    assert dereferenced["properties"]["parent"]["_is_cycle"] is True


def test_openapi_parser():
    """Verify complete parsing into normalized models."""
    parser = OpenAPIParser(SAMPLE_OPENAPI_SPEC)
    spec_model = parser.parse()

    assert spec_model.title == "Payment API"
    assert spec_model.version == "1.0.0"
    assert len(spec_model.servers) == 1
    assert len(spec_model.operations) == 1

    op = spec_model.operations[0]
    assert op.method == "post"
    assert op.path == "/api/v1/payments"
    assert op.request_body is not None
    assert op.request_body.schema is not None
    assert op.request_body.schema.type == "object"
    assert "amount" in op.request_body.schema.properties
    assert op.request_body.schema.properties["amount"].minimum == 0.01
