# Schema Boundary Fuzzing

SpecForge's core innovation is **active quality verification**. Rather than passively rendering API documentation, SpecForge algorithmically analyzes every JSON Schema rule on your endpoints and constructs targeted boundary test cases.

---

## The "Zero 500s" Invariant

In modern web development, clients send bad, missing, or malformed data all the time. 

- **Good Behavior**: The server catches the validation failure and returns a structured `400 Bad Request` or `422 Unprocessable Entity`.
- **Dangerous Behavior**: The application crashes with an unhandled exception, leaking stack traces, creating log noise, and returning `500 Internal Server Error`.

SpecForge runs automated boundary tests specifically to prove your API upholds the **Zero 500s Invariant**: no edge-case input should ever produce an unhandled server exception.

---

## Automated Fuzzing Strategies by Type

SpecForge inspects parameter and request body schemas to synthesize edge cases:

### 1. String Fields
* **Whitespace Only**: Probes whether your backend strips strings (e.g. `"   "`). Catches database errors when blank strings bypass `min_length` or unique constraints.
* **Empty String**: Tests `""` when a field is required or non-empty.
* **Length Boundaries**: Exact `min_length - 1` (underflow) and `max_length + 1` (overflow).
* **Format Violations**: Synthesizes invalid formats for `email`, `uuid`, `date`, `date-time`, and `uri`.
* **Dangerous Payloads**: Checks for null-byte injection (`\x00`), Unicode 4-byte astral characters (emojis), and long strings.

### 2. Number & Integer Fields
* **Boundaries**: Generates values at `minimum - 1` and `maximum + 1`.
* **Negative Values**: Sends negative values against unsigned counters or prices.
* **Type Pollution**: Injects floating-point decimals into strict integer fields.
* **Extreme Numbers**: Tests standard integer overflow numbers (`2^31 - 1`, `2^63 - 1`).

### 3. Object & Body Schemas
* **Combinatorial Required Field Omission**: Strips each required field one by one to verify the server returns clean field-level error messages.
* **Unexpected Keys (`additionalProperties`)**: Injects extra, undeclared fields to detect mass-assignment vulnerabilities.
* **Empty Payloads**: Tests sending `{}` when fields are expected.

### 4. Array Fields
* **Boundary Sizing**: Probes `minItems - 1` and `maxItems + 1`.
* **Duplicate Items**: Injects duplicate items when `uniqueItems: true` is set.
* **Empty Arrays**: Sends `[]` to test empty container validation.

---

## Running Boundary Tests in the UI

1. Open `/docs` in your browser.
2. Select any operation in the left sidebar (e.g. `POST /users`).
3. Scroll down to the **Automated Contract Tests** section.
4. Click **Run All Invariant Tests**.
5. SpecForge will execute the suite in real-time, displaying passing invariants in green and flagging any `500 Server Crashes` in red with full cURL reproduction snippets!
