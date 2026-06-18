# OIC OpenAPI → XSD Generator

Generate **XML Schema (XSD)** and **JSON Schema** files from **OpenAPI 3.x** specifications for use with **Oracle Integration Cloud (OIC) Gen3** REST adapters.

The tool keeps OpenAPI as the single source of truth and produces OIC-ready polymorphic response XSDs, plain request XSDs, and merged JSON schemas for documentation and validation.

## Author

Created by **[Maxime Frankefort](https://github.com/maaxx888)**

## Related documentation

| Document | Purpose |
|----------|---------|
| [SUPPORTED_TYPES.md](SUPPORTED_TYPES.md) | Full OpenAPI type and format → XSD mapping |
| [API-guide.md](API-guide.md) | OIC Gen3 + API Gateway integration patterns |

---

## Features

- **Response XSD** — polymorphic envelope with `status` (SUCCESS/FAILED), data field, and `errors`
- **Request XSD** — plain payload schema for POST, PUT, PATCH, DELETE (skipped for GET)
- **JSON schemas** — saved alongside XSD files; response schemas merge success + error responses
- **Reference resolution** — resolves `$ref` within OpenAPI documents via `jsonref`
- **Format support** — JSON and YAML OpenAPI input
- **Type mapping** — dates, numbers, enums, nested objects, arrays (see [SUPPORTED_TYPES.md](SUPPORTED_TYPES.md))
- **Documentation in XSD** — field descriptions from OpenAPI become XML comments
- **Deduplication** — avoids duplicate type definitions within a single generated schema

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

python3 oic_xsd_gen.py test-input/sample-api-v1.0.0.json
```

Output appears under `generated/sample-api-v1.0.0/schemas/`.

---

## Installation

### Prerequisites

- Python 3.10+
- `pip`

### Steps

```bash
cd /path/to/oic-openapi-xsd-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 oic_xsd_gen.py --help
```

Dependencies (`requirements.txt`):

- `pyyaml` — YAML parsing
- `jsonref` — JSON reference resolution

---

## Usage

### Basic

```bash
python3 oic_xsd_gen.py <openapi-file>
```

Example:

```bash
python3 oic_xsd_gen.py test-input/partijhub-api-v1.0.0.json
```

### Custom output directory

```bash
python3 oic_xsd_gen.py <openapi-file> -o /path/to/output
```

If `-o` is omitted, output goes to `./generated/<spec-stem>/` (the OpenAPI filename without extension).

### CLI reference

```
usage: oic_xsd_gen.py [-h] [-o OUTPUT] openapi_path

positional arguments:
  openapi_path         Path to the OpenAPI JSON or YAML document.

options:
  -h, --help           show this help message and exit
  -o, --output OUTPUT  Output folder. Default: ./generated/<spec-stem>
```

---

## Output structure

```
generated/
└── sample-api-v1.0.0/
    └── schemas/
        ├── request/
        │   ├── create-item-request.xsd
        │   └── create-item-request.json
        ├── response/
        │   ├── create-item-response.xsd
        │   ├── create-item-response.json
        │   └── get-item-by-id-response.json
        └── error/
            └── create-item-error-response.json
```

| File | Purpose | When generated |
|------|---------|----------------|
| `*-response.xsd` | Polymorphic response schema for OIC (handles both success + error) | Every operation |
| `*-request.xsd` | Plain request body schema | POST, PUT, PATCH, DELETE with JSON body |
| `response/*-response.json` | Success response schema (status=SUCCESS only) | Every operation |
| `error/*-error-response.json` | Error response schema (status=FAILED only) | Operations with 4xx/5xx error responses |
| `*-request.json` | Request body JSON schema | Same as request XSD |

**Note:** JSON schemas are **reference only** for documentation; OIC uses the XSD files. Success and error response schemas are kept separate for clarity.

---

## OpenAPI requirements

### 1. `operationId` (required)

Every operation must have a unique `operationId`. It drives XSD type names and file names.

```json
{
  "get": {
    "operationId": "getPersonByPartyNumber",
    ...
  }
}
```

Use camelCase: `getPersonByPartyNumber`, `createItem`.

### 2. Success response (200 or 201)

Every operation needs a `200` (GET/PUT/PATCH) or `201` (POST) response with an `application/json` schema.

### 3. Status envelope (response schemas)

Response schemas should follow the OIC polymorphic pattern:

```json
{
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["SUCCESS", "FAILED"]
    },
    "<data-field>": {
      "type": "object",
      "properties": { ... }
    },
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "code": { "type": "string" },
          "message": { "type": "string" },
          "details": { "type": "object" }
        }
      }
    }
  }
}
```

The generator detects the **first property** that is not `status` or `errors` as the data field (e.g. `person`, `item`, `data`).

### 4. Request body (optional)

Define `requestBody` with `application/json` for operations that accept a body. GET operations are skipped automatically.

### 5. Descriptions (recommended)

Add `description` on properties and operations. These become XML comments in the XSD.

---

## Type mapping

The generator maps OpenAPI JSON Schema types to XSD. Highlights:

| JSON Schema | Format | XSD type |
|-------------|--------|----------|
| `string` | — | `xs:string` |
| `string` | `date` | `xs:date` |
| `string` | `date-time` | `xs:dateTime` |
| `string` | `time` | `xs:time` |
| `string` | `duration` | `xs:duration` |
| `integer` | `int32` / (none) | `xs:int` |
| `integer` | `int64` | `xs:long` |
| `number` | — | `xs:decimal` |
| `number` | `float` | `xs:float` |
| `number` | `double` | `xs:double` |
| `boolean` | — | `xs:boolean` |
| `string` | `byte` / `binary` | `xs:hexBinary` or `xs:base64Binary` |
| `array` | — | child type with `maxOccurs="unbounded"` |
| `object` | — | nested `xs:complexType` |
| enum | — | `xs:simpleType` with `xs:enumeration` |

Full mapping table: [SUPPORTED_TYPES.md](SUPPORTED_TYPES.md).

---

## Response XSD structure

```xml
<xs:complexType name="GetPersonByPartyNumberResponseType">
  <xs:sequence>
    <xs:element name="status" type="StatusType" minOccurs="1" maxOccurs="1" />
    <xs:element name="person" type="PersonResponseType" minOccurs="0" maxOccurs="1" />
    <xs:element name="errors" type="ErrorItemType" minOccurs="0" maxOccurs="unbounded" />
  </xs:sequence>
</xs:complexType>
```

- `status` — always required (`minOccurs="1"`)
- data field — optional in XSD (`minOccurs="0"`) because it is absent on FAILED
- `errors` — unbounded array (`maxOccurs="unbounded"`)

Request XSDs are plain structures without the status envelope.

---

## Test inputs

| File | What it exercises |
|------|-------------------|
| `test-input/sample-api-v1.0.0.json` | GET + POST with request/response |
| `test-input/partijhub-api-v1.0.0.json` | GET-only government-style envelope |
| `test-input/comprehensive-types-api-v1.0.0.json` | All supported OpenAPI types and formats |
| `test-input/constraints-api-v1.0.0.json` | `pattern`, lengths, bounds, `allOf`, `oneOf`, merged errors |

```bash
python3 oic_xsd_gen.py test-input/comprehensive-types-api-v1.0.0.json
python3 -m pytest tests/ -v
```

---

## OIC Gen3 integration

For step-by-step OIC setup (REST adapter trigger, XSD upload, mapping, fault handling), see [API-guide.md](API-guide.md).

Summary:

1. Generate XSD files with this tool
2. Upload `*-response.xsd` as the REST trigger **response** schema
3. Select the root element (e.g. `GetPersonByPartyNumberResponse`)
4. Upload `*-request.xsd` for POST/PUT/PATCH if request validation is needed
5. Map success path → `status=SUCCESS` + data fields; fault path → `status=FAILED` + `errors`

---

## Troubleshooting

### Missing `operationId`

```
Skipped operations:
- unknown operation (GET /v1/persons/{partyNumber})
  Reason: Missing operationId
```

Add `operationId` to the operation.

### No 200 or 201 success response

Define `200` or `201` in `responses` with a JSON schema.

### No `application/json` schema on success response

Ensure the success response has `content.application/json.schema`.

### Data property must be object or array

The envelope data field (first non-`status`/`errors` property) must be an object or array, not a primitive.

### `Object of type dict is not JSON serializable`

Usually a `$ref` resolution issue. Validate your spec:

```bash
python3 -m json.tool test-input/sample-api-v1.0.0.json > /dev/null
```

---

## Known limitations

| Area | Current behavior |
|------|------------------|
| `multipleOf` | Documented in XSD comments only (XSD 1.0 limitation) |
| `oneOf` / `anyOf` with incompatible branches | Object branches are merged into a superset; discriminators are not enforced |
| `additionalProperties: false` | Preserved in JSON schema; noted in XSD comments, not enforced in XSD |
| Path/query/header parameters | Not generated as separate schemas |
| Non-JSON content types | Only `application/json` and `*+json` |
| Shared component types | Deduplicated per schema file via parent-prefixed type names |

Supported constraints (`pattern`, `minLength`, `maxLength`, numeric bounds, `enum`, `minItems`/`maxItems`, `allOf`, `oneOf`, `anyOf`, nullable) are documented in [SUPPORTED_TYPES.md](SUPPORTED_TYPES.md).

---

## Project layout

```
oic-openapi-xsd-generator/
├── oic_xsd_gen.py          # Main generator
├── requirements.txt
├── README.md
├── SUPPORTED_TYPES.md
├── API-guide.md
├── test-input/             # Sample OpenAPI specs
└── generated/              # Default output (created on run)
```

OpenAPI specs for your APIs can live anywhere; pass the path to the CLI. A common convention (used in broader integration repos) is `apis/<project>/spec/*.json`.

---

## Batch processing

Process multiple specs with a simple loop:

```bash
for spec in test-input/*.json; do
  python3 oic_xsd_gen.py "$spec"
done
```

For CI/CD, run the generator after OpenAPI changes and commit the `generated/` output alongside the spec.

---

## License

Apache License 2.0. See [LICENSE](LICENSE) file for details.

---

## References

- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.3)
- [XML Schema (XSD)](https://www.w3.org/TR/xmlschema-1/)
- [Oracle Integration Cloud](https://docs.oracle.com/en/cloud/paas/integration-cloud/)
