# Configuration Reference

SpecForge is configured using the `SpecForgeConfig` dataclass or by passing keyword arguments directly to the framework adapters (`SpecForge(app, ...)`).

---

## Configuration Options

| Option | Type | Default | Description |
|---|---|---|---|
| `spec_url` | `str` | `"/openapi.json"` | Path or URL to the OpenAPI specification. |
| `path` | `str` | `"/docs"` | The HTTP route where the SpecForge studio will be served. |
| `title` | `str` | `"SpecForge - API Explorer & Quality Gate"` | Browser title displayed in the tab bar. |
| `theme` | `str` | `"theme-1"` | Initial UI color palette (`theme-1`: Indigo Slate, `theme-2`: Emerald Teal, `theme-3`: Midnight Dark, `theme-4`: Cobalt Blue). |
| `read_only` | `bool` | `False` | Disables sending requests or executing invariant tests from the browser. |
| `test_paths` | `list[str]` | `[]` | List of directory paths or test files to scan for existing tests. |
| `base_url` | `str \| None` | `None` | Default API target host when executing requests (defaults to current browser origin). |
| `hide_internal_models` | `bool` | `False` | Hides schemas prefixed with an underscore or tagged as internal. |

---

## Example Usage with `SpecForgeConfig`

```python
from fastapi import FastAPI
from specforge import SpecForge, SpecForgeConfig

app = FastAPI()

config = SpecForgeConfig(
    path="/api-docs",
    title="Core Platform Studio",
    theme="theme-2",
    test_paths=["tests/contract", "tests/unit"],
)

SpecForge(app, config=config)
```
