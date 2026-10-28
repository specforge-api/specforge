"""JSON Pointer & $ref reference resolver with circular reference protection."""

from typing import Any, Optional


class RefResolver:
    """Resolves JSON Reference ($ref) pointers within an OpenAPI specification."""

    def __init__(self, root_spec: dict[str, Any], max_depth: int = 25):
        self.root_spec = root_spec
        self.max_depth = max_depth

    def resolve_pointer(self, ref: str) -> dict[str, Any]:
        """Resolve a local JSON Pointer string like '#/components/schemas/User'.

        Raises ValueError if the reference cannot be located.
        """
        if not ref.startswith("#/"):
            raise ValueError(f"External references are not supported: {ref}")

        parts = ref[2:].split("/")
        current: Any = self.root_spec

        for part in parts:
            # Unescape JSON pointer tokens (~1 for /, ~0 for ~)
            part = part.replace("~1", "/").replace("~0", "~")
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
                current = current[int(part)]
            else:
                raise ValueError(f"Could not resolve $ref pointer part '{part}' in '{ref}'")

        if not isinstance(current, dict):
            return {"type": "object", "value": current}
        return current

    def dereference(
        self,
        schema: Any,
        visited_refs: Optional[set[str]] = None,
        depth: int = 0,
    ) -> Any:
        """Recursively dereferences schemas, protecting against infinite cyclic references."""
        if visited_refs is None:
            visited_refs = set()

        if depth > self.max_depth:
            return {"type": "object", "description": "[Recursion depth exceeded]"}

        if not isinstance(schema, dict):
            if isinstance(schema, list):
                return [self.dereference(item, visited_refs, depth + 1) for item in schema]
            return schema

        # Check for $ref
        if "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path in visited_refs:
                # Cycle detected! Return a stub to avoid infinite recursion
                model_name = ref_path.split("/")[-1]
                return {
                    "type": "object",
                    "description": f"[Circular reference to {model_name}]",
                    "_is_cycle": True,
                }

            resolved = self.resolve_pointer(ref_path)
            new_visited = visited_refs.copy()
            new_visited.add(ref_path)

            # Dereference the target schema
            dereferenced_target = self.dereference(resolved, new_visited, depth + 1)

            # Merge any local overrides in the original schema (e.g. description, nullable)
            merged = dict(dereferenced_target)
            for k, v in schema.items():
                if k != "$ref":
                    merged[k] = v
            return merged

        # Otherwise, recursively dereference dictionary keys
        result: dict[str, Any] = {}
        for key, val in schema.items():
            if key in ("properties", "patternProperties") and isinstance(val, dict):
                result[key] = {
                    prop_name: self.dereference(prop_schema, visited_refs, depth + 1)
                    for prop_name, prop_schema in val.items()
                }
            elif key == "items":
                result[key] = self.dereference(val, visited_refs, depth + 1)
            elif key in ("allOf", "anyOf", "oneOf") and isinstance(val, list):
                result[key] = [self.dereference(item, visited_refs, depth + 1) for item in val]
            elif isinstance(val, dict):
                result[key] = self.dereference(val, visited_refs, depth + 1)
            elif isinstance(val, list):
                result[key] = [self.dereference(item, visited_refs, depth + 1) for item in val]
            else:
                result[key] = val

        return result
