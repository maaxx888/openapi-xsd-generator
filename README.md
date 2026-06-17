# OIC OpenAPI → XSD Generator

Automatically generate OIC Gen3-compatible XSD schemas from OpenAPI 3.x specifications. Handles both **response schemas** (with status envelope) and **request schemas** (plain payload).

## Features

- **Response XSD**: Generates polymorphic XSD with status envelope (SUCCESS/FAILED) and optional error details
- **Request XSD**: Generates request body XSD for POST, PUT, PATCH, DELETE operations
- **GET Requests**: Skips request XSD generation (no request body)
- **Reference Resolution**: Automatically resolves `$ref` links within OpenAPI documents
- **YAML & JSON Support**: Accepts both `.yaml` and `.json` OpenAPI specifications
- **Validated**: Extracts operationId, request/response schemas, and generates clean XSD output

## Installation

### Prerequisites
- Python 3.10+
- Virtual environment (recommended)

### Setup

```bash
cd oic-openapi-xsd-generator
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python3 oic_xsd_gen.py <openapi-file>
```

Example:
```bash
python3 oic_xsd_gen.py apis/partijhub/spec/partijhub-api-v1.0.0.json
```

### Output Location

By default, generated files are saved in `./generated/<spec-name>/`:

```
generated/
├── partijhub-api-v1.0.0/
│   └── schemas/
│       ├── json/
│       │   ├── get-person-by-party-number-response.schema.json
│       │   └── create-item-request.schema.json
│       ├── request/
│       │   └── create-item-request.xsd
│       └── response/
│           ├── get-person-by-party-number-response.xsd
│           └── create-item-response.xsd
```

### Custom Output Directory

```bash
python3 oic_xsd_gen.py apis/partijhub/spec/partijhub-api-v1.0.0.json -o ./my-schemas
```

## Operation Support

### GET Operations
- **Response XSD**: ✅ Generated
- **Request XSD**: ❌ Skipped (no request body in GET)

### POST / PUT / PATCH / DELETE Operations
- **Response XSD**: ✅ Generated (with status envelope)
- **Request XSD**: ✅ Generated (if requestBody defined in OpenAPI)

## OpenAPI Requirements

For the tool to generate XSD files, your OpenAPI spec must:

1. **Have operationId** on every operation
   ```json
   "get": {
     "operationId": "getPersonByPartyNumber",
     ...
   }
   ```

2. **Define success response** (200 or 201 with application/json schema)
   ```json
   "responses": {
     "200": {
       "content": {
         "application/json": {
           "schema": { "$ref": "#/components/schemas/PersonResponse" }
         }
       }
     }
   }
   ```

3. **Response schema has status envelope** (for response XSD)
   ```json
   {
     "type": "object",
     "properties": {
       "status": { "enum": ["SUCCESS", "FAILED"] },
       "person": { ... },
       "errors": { "type": "array", "items": { ... } }
     },
     "required": ["status"]
   }
   ```

4. **Request body defined** (for POST/PUT/PATCH request XSD)
   ```json
   "post": {
     "operationId": "createItem",
     "requestBody": {
       "required": true,
       "content": {
         "application/json": {
           "schema": { "$ref": "#/components/schemas/CreateItemRequest" }
         }
       }
     }
   }
   ```

## Output XSD Format

### Response XSD (with Status Envelope)

```xml
<xs:complexType name="GetPersonResponseType">
  <xs:sequence>
    <!-- Always present: SUCCESS or FAILED -->
    <xs:element name="status" type="StatusType" minOccurs="1" maxOccurs="1"/>
    <!-- Filled on SUCCESS -->
    <xs:element name="person" type="PersonResponseType" minOccurs="0" maxOccurs="1"/>
    <!-- Filled on FAILED; maxOccurs=unbounded → JSON array -->
    <xs:element name="errors" type="ErrorItemType" minOccurs="0" maxOccurs="unbounded"/>
  </xs:sequence>
</xs:complexType>
```

### Request XSD (Plain Payload)

```xml
<xs:complexType name="CreateItemRequestType">
  <xs:sequence>
    <xs:element name="name" type="xs:string" minOccurs="1" maxOccurs="1"/>
    <xs:element name="description" type="xs:string" minOccurs="0" maxOccurs="1"/>
    <xs:element name="price" type="xs:decimal" minOccurs="1" maxOccurs="1"/>
  </xs:sequence>
</xs:complexType>
```

## Type Mapping

| JSON Schema Type | XSD Type |
|---|---|
| `string` | `xs:string` |
| `integer` (int32) | `xs:int` |
| `integer` (int64) | `xs:long` |
| `number` | `xs:decimal` |
| `boolean` | `xs:boolean` |
| `object` | `xs:complexType` |
| `array` of objects | `xs:element` with `maxOccurs="unbounded"` |
| `enum` | `xs:simpleType` with `xs:enumeration` |

## Examples

### Example 1: GET Operation (Response Only)

**OpenAPI:**
```json
{
  "paths": {
    "/v1/persons/{partyNumber}": {
      "get": {
        "operationId": "getPersonByPartyNumber",
        "responses": {
          "200": { "$ref": "#/components/responses/PersonOkResponse" }
        }
      }
    }
  }
}
```

**Generated Files:**
- `schemas/response/get-person-by-party-number-response.xsd` (response only)

### Example 2: POST Operation (Request + Response)

**OpenAPI:**
```json
{
  "paths": {
    "/items": {
      "post": {
        "operationId": "createItem",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/CreateItemRequest" }
            }
          }
        },
        "responses": {
          "201": { "$ref": "#/components/responses/ItemCreatedResponse" }
        }
      }
    }
  }
}
```

**Generated Files:**
- `schemas/request/create-item-request.xsd` (request)
- `schemas/response/create-item-response.xsd` (response)

## Testing

### Run with Test Data

```bash
# Test with PartijHub API (GET only)
python3 oic_xsd_gen.py test-input/partijhub-api-v1.0.0.json

# Test with sample API (GET + POST)
python3 oic_xsd_gen.py test-input/sample-api-v1.0.0.json
```

### Verify Generated XSD

```bash
cat generated/sample-api-v1.0.0/schemas/request/create-item-request.xsd
cat generated/sample-api-v1.0.0/schemas/response/create-item-response.xsd
```

## Integration with OIC Gen3

1. Generate XSD files using this tool
2. Upload response XSD to OIC REST adapter trigger:
   - Configure Response Payload as XML
   - Upload XSD file
   - Select root element (e.g., `GetPersonResponse`)
3. (Optional) Use request XSD to validate incoming requests:
   - Upload request XSD to trigger request validation

## Troubleshooting

### "Missing operationId"
- Every operation must have an `operationId` field
- Add it to your OpenAPI spec under each operation

### "No 200 or 201 success response found"
- Ensure your operation has a `200` or `201` response
- Both responses must contain an `application/json` schema

### "Could not detect the data property"
- Response schema must have a `status` field and at least one data property
- Example: `{ "status": "SUCCESS", "person": {...} }` or `{ "status": "SUCCESS", "items": [...] }`

### File not found error
- Use absolute paths or verify relative path is correct
- Example: `python3 oic_xsd_gen.py /full/path/to/api-spec.json`

## References

- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.3)
- [XML Schema (XSD) Reference](https://www.w3.org/TR/xmlschema-1/)
- [OIC Gen3 Integration Guide](./API-guide.md)
