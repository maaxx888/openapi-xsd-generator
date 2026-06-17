# OIC OpenAPI → XSD Generator

## Executive Summary

This tool automates the generation of **XML Schema Definition (XSD)** files from **OpenAPI 3.x** specifications for use with **Oracle Integration Cloud (OIC) Gen3** REST adapters. It is designed for government and enterprise integrations requiring strict schema validation, clear documentation, and compliance with integration standards.

The tool eliminates manual XSD creation, ensuring consistency, reducing human error, and maintaining a single source of truth between your OpenAPI specification and OIC runtime schemas.

### Key Benefits
- **Automation**: Generate XSD from OpenAPI in seconds (no manual XML coding)
- **Consistency**: Ensures all integrations follow the same schema pattern
- **Documentation**: Automatic comment extraction from OpenAPI descriptions
- **Compliance**: Validates against OIC Gen3 polymorphic schema requirements
- **Traceability**: Keep OpenAPI spec and XSD in version control, always in sync
- **Government-Ready**: Suitable for government digital services with clear audit trails

---

## Features

### Core Features
- **Response XSD Generation**: Polymorphic XSD with status envelope (SUCCESS/FAILED) for all operations
- **Request XSD Generation**: Plain payload XSD for POST, PUT, PATCH, DELETE operations
- **GET Optimization**: Automatically skips request XSD (no request body in HTTP GET)
- **Reference Resolution**: Fully resolves `$ref` links within OpenAPI documents (internal and external)
- **Format Support**: Accepts both JSON and YAML OpenAPI specifications
- **Deduplication**: Prevents duplicate type definitions in generated XSD

### Documentation Features
- **Automatic Comments**: Extracts field descriptions from OpenAPI schema
- **Self-Documenting**: Generated XSD includes documentation for maintainability
- **Type Information**: Clear XSD type information with minOccurs/maxOccurs constraints
- **Enumeration Details**: All enum values documented with descriptions

### Enterprise Features
- **Batch Processing**: Process multiple OpenAPI files programmatically
- **Custom Output Directories**: Control where generated files are stored
- **Clear Reporting**: Detailed output showing what was generated and what was skipped
- **Error Handling**: Graceful failure with actionable error messages
- **Validation**: Checks for required OpenAPI elements before generation

---

## Architecture Overview

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Your Development Process                    │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
          ┌─────────────────────────────────────────┐
          │   1. Create/Update OpenAPI Spec         │
          │   - Define paths, operations            │
          │   - Add descriptions for fields         │
          │   - Define request/response schemas     │
          │   - File: apis/{domain}/spec/*.json     │
          └─────────────────────────────────────────┘
                                 ↓
          ┌─────────────────────────────────────────┐
          │   2. Run XSD Generation                 │
          │   python3 oic_xsd_gen.py <file>        │
          └─────────────────────────────────────────┘
                                 ↓
          ┌─────────────────────────────────────────┐
          │   3. Review Generated XSD Files         │
          │   - Response XSD (polymorphic)          │
          │   - Request XSD (plain)                 │
          │   - JSON schemas (for reference)        │
          └─────────────────────────────────────────┘
                                 ↓
          ┌─────────────────────────────────────────┐
          │   4. Upload to OIC Gen3                 │
          │   - Configure REST adapter trigger      │
          │   - Select response XSD as schema       │
          │   - Select root element                 │
          └─────────────────────────────────────────┘
                                 ↓
          ┌─────────────────────────────────────────┐
          │   5. OIC Runtime Validation             │
          │   - Incoming requests validated         │
          │   - Response payload mapped to XSD      │
          │   - XML ↔ JSON conversion automatic     │
          └─────────────────────────────────────────┘
```

### OIC Gen3 Runtime Workflow

```
Client Request
        ↓
    API Gateway (OAuth2, routing)
        ↓
    OIC REST Adapter Trigger
    ├─ Request: Validate against request XSD (if POST/PUT/PATCH)
    ├─ Invoke backend integration
    └─ Response Mapping:
        ├─ Success path: status="SUCCESS" + data fields (mapped from response XSD)
        ├─ Fault path: status="FAILED" + error entries
        └─ Convert XML to JSON (automatic, XSD-driven)
        ↓
    API Gateway
        ↓
    Client Response (JSON with status + data/errors)
```

---

## Installation & Setup

### Prerequisites
- **Python 3.10 or higher** (check with `python3 --version`)
- **pip** (Python package manager, typically included with Python)
- **Virtual environment** (recommended for isolation)

### Step-by-Step Installation

#### 1. Clone or Download the Tool

```bash
cd /path/to/oic-openapi-xsd-generator
```

#### 2. Create Virtual Environment

```bash
python3 -m venv .venv
```

This creates an isolated Python environment for dependencies.

#### 3. Activate Virtual Environment

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows (PowerShell):**
```bash
.venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```bash
.venv\Scripts\activate.bat
```

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs required packages:
- `pyyaml` — YAML file parsing
- `jsonref` — JSON reference resolution

#### 5. Verify Installation

```bash
python3 oic_xsd_gen.py --help
```

You should see the help message confirming the tool is ready.

**Expected Output:**
```
usage: oic_xsd_gen.py [-h] [-o OUTPUT] openapi_file

OIC XSD Generator - Convert OpenAPI to XSD for OIC Gen3

positional arguments:
  openapi_file          Path to OpenAPI specification (JSON or YAML)

optional arguments:
  -h, --help            Show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory (default: ./generated)
```

#### 6. Run a Quick Test

Test with the included test file (if available):

```bash
python3 oic_xsd_gen.py test-input/sample-spec.json
```

Check the output:
```bash
ls -la generated/
```

You should see:
- `generated/{spec-name}/schemas/response/` — Response XSD files
- `generated/{spec-name}/schemas/request/` — Request XSD files (if POST/PUT/PATCH operations exist)
- `generated/{spec-name}/schemas/json/` — JSON schemas (reference only)

---

## Usage Guide

### Basic Usage

```bash
python3 oic_xsd_gen.py <openapi-file>
```

**Example:**
```bash
python3 oic_xsd_gen.py apis/partijhub/spec/partijhub-api-v1.0.0.json
```

**Output:**
- Generated files are saved to `./generated/<spec-name>/` by default
- Each operation gets a response XSD
- POST/PUT/PATCH/DELETE operations also get request XSD
- JSON schemas are saved for reference

### Custom Output Directory

```bash
python3 oic_xsd_gen.py <openapi-file> -o /path/to/custom/output
```

**Example:**
```bash
python3 oic_xsd_gen.py apis/partijhub/spec/partijhub-api-v1.0.0.json -o ./generated-schemas
```

### Output Directory Structure

```
generated/
├── partijhub-api-v1.0.0/
│   └── schemas/
│       ├── json/
│       │   ├── get-person-by-party-number-response.schema.json
│       │   ├── get-person-by-party-number-request.schema.json  (if applicable)
│       │   └── ... (one per operation)
│       ├── request/
│       │   ├── create-item-request.xsd
│       │   └── ... (POST/PUT/PATCH/DELETE only)
│       └── response/
│           ├── get-person-by-party-number-response.xsd
│           ├── create-item-response.xsd
│           └── ... (all operations)
```

### Important File Descriptions

| File Type | Purpose | When Generated | OIC Usage |
|-----------|---------|-----------------|-----------|
| `*-response.xsd` | Response schema with status envelope | All operations (GET, POST, PUT, PATCH, DELETE) | **Upload as REST adapter trigger response schema** |
| `*-request.xsd` | Request body schema (plain, no envelope) | POST, PUT, PATCH, DELETE only | Optional: Validate incoming request payloads |
| `*.schema.json` | JSON schema (reference only) | All operations | Not used by OIC, kept for documentation |

---

## OpenAPI Specification Requirements

The tool requires specific elements in your OpenAPI specification to generate valid XSD files. This section details all requirements.

### 1. Operation Must Have `operationId`

**Required:** Every operation must have a unique `operationId`

**Why:** The `operationId` is used as the base name for generated XSD types and file names.

**Example:**
```json
{
  "paths": {
    "/v1/persons/{partyNumber}": {
      "get": {
        "operationId": "getPersonByPartyNumber",
        "description": "Retrieves person data by party number",
        ...
      }
    }
  }
}
```

**Naming Convention:** Use camelCase with verb + noun pattern
- ✅ Good: `getPersonByPartyNumber`, `createInvoice`, `updateBankBranch`
- ❌ Bad: `getPerson`, `get_person`, `GetPerson`, `person_get`

### 2. Success Response Must Be Defined (200 or 201)

**Required:** Every operation must have a `200` (GET/PUT/PATCH) or `201` (POST) response with JSON schema

**Why:** The response schema drives XSD generation and tells OIC what the response payload looks like.

**Example:**
```json
{
  "responses": {
    "200": {
      "description": "Operation successful",
      "content": {
        "application/json": {
          "schema": { "$ref": "#/components/schemas/PersonResponse" }
        }
      }
    },
    "400": {
      "description": "Bad request",
      "content": {
        "application/json": {
          "schema": { "$ref": "#/components/schemas/ErrorResponse" }
        }
      }
    }
  }
}
```

### 3. Response Schema Must Use Status Envelope

**Required:** All response schemas must follow the polymorphic envelope pattern with `status`, data, and `errors` fields.

**Why:** OIC Gen3 uses a single XSD for both success and error responses. The `status` field discriminates between them.

**Structure:**
```json
{
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["SUCCESS", "FAILED"],
      "description": "Operation outcome"
    },
    "<data-field>": {
      "type": "object",
      "description": "Response data (present on SUCCESS)",
      "properties": { ... }
    },
    "errors": {
      "type": "array",
      "description": "Error details (present on FAILED)",
      "items": {
        "type": "object",
        "properties": {
          "code": { "type": "string", "description": "Error code" },
          "message": { "type": "string", "description": "Error message" },
          "details": { "type": "object", "description": "Backend-specific details" }
        }
      }
    }
  },
  "additionalProperties": false
}
```

**Example — Success Response:**
```json
{
  "status": "SUCCESS",
  "person": {
    "partyNumber": "KSZ:80010120990",
    "firstName": "John",
    "lastName": "Doe",
    "birthDate": "1980-01-12"
  }
}
```

**Example — Error Response:**
```json
{
  "status": "FAILED",
  "errors": [
    {
      "code": "PERSON_NOT_FOUND",
      "message": "No person found for KSZ:80010120990",
      "details": {
        "identification": "MAGDA_ERROR_123",
        "diagnose": "Person record not in system"
      }
    }
  ]
}
```

### 4. Request Body for POST/PUT/PATCH (Optional but Recommended)

**Required for:** POST, PUT, PATCH, DELETE operations that accept a request body

**Optional for:** GET operations (they have no request body)

**Why:** Allows the tool to generate request XSD for validating incoming payloads.

**Structure:**
```json
{
  "paths": {
    "/items": {
      "post": {
        "operationId": "createItem",
        "requestBody": {
          "required": true,
          "description": "Item data to create",
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/CreateItemRequest" }
            }
          }
        },
        "responses": { ... }
      }
    }
  }
}
```

### 5. Add Descriptions for Better XSD Comments (Recommended)

**Optional but strongly recommended:** Add `description` fields to all schema properties.

**Why:** These are extracted and added as XML comments in the generated XSD, making it self-documenting.

**Example:**
```json
{
  "type": "object",
  "properties": {
    "firstName": {
      "type": "string",
      "description": "First given name from MAGDA → Oracle HZ_PERSON_PROFILES.PERSON_FIRST_NAME"
    },
    "birthDate": {
      "type": "string",
      "format": "date",
      "description": "Date of birth in ISO 8601 format (YYYY-MM-DD)"
    },
    "status": {
      "type": "string",
      "enum": ["ACTIVE", "INACTIVE"],
      "description": "Account status: ACTIVE for current accounts, INACTIVE for archived"
    }
  }
}
```

**Generated XSD includes:**
```xml
<!-- First given name from MAGDA → Oracle HZ_PERSON_PROFILES.PERSON_FIRST_NAME -->
<xs:element name="firstName" type="xs:string" minOccurs="1" maxOccurs="1" />

<!-- Date of birth in ISO 8601 format (YYYY-MM-DD) -->
<xs:element name="birthDate" type="xs:string" minOccurs="0" maxOccurs="1" />

<!-- Account status: ACTIVE for current accounts, INACTIVE for archived -->
<xs:element name="status" type="StatusType" minOccurs="1" maxOccurs="1" />
```

### 6. Proper JSON Schema Patterns

**Required:** All schemas must follow JSON Schema conventions

#### Use `required` Array for Mandatory Fields
```json
{
  "type": "object",
  "properties": {
    "firstName": { "type": "string" },
    "lastName": { "type": "string" },
    "middleName": { "type": "string" }
  },
  "required": ["firstName", "lastName"],
  "additionalProperties": false
}
```

Generated XSD:
- `firstName` → `minOccurs="1"` (required)
- `lastName` → `minOccurs="1"` (required)
- `middleName` → `minOccurs="0"` (optional)

#### Use `enum` for Constrained Values
```json
{
  "type": "string",
  "enum": ["01", "02", "03"],
  "description": "Register type code"
}
```

Generated XSD creates a `simpleType` with enumeration restrictions:
```xml
<xs:simpleType name="RegisterCodeType">
  <xs:restriction base="xs:string">
    <xs:enumeration value="01" />
    <xs:enumeration value="02" />
    <xs:enumeration value="03" />
  </xs:restriction>
</xs:simpleType>
```

#### Use Proper Type Declarations
```json
{
  "type": "object",
  "properties": {
    "price": {
      "type": "number",
      "description": "Price amount"
    },
    "quantity": {
      "type": "integer",
      "format": "int32",
      "description": "Quantity"
    },
    "count": {
      "type": "integer",
      "format": "int64",
      "description": "Large number"
    },
    "isActive": {
      "type": "boolean",
      "description": "Active flag"
    }
  }
}
```

Generated XSD type mapping:
| JSON Type | Format | XSD Type |
|-----------|--------|----------|
| `string` | (any) | `xs:string` |
| `integer` | `int32` | `xs:int` |
| `integer` | `int64` | `xs:long` |
| `number` | (any) | `xs:decimal` |
| `boolean` | (any) | `xs:boolean` |

---

## Output XSD Format & Examples

### Response XSD Structure

All response XSDs follow the **polymorphic pattern** for OIC Gen3:

```xml
<?xml version='1.0' encoding='utf-8'?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="unqualified">
  
  <!-- Root Element -->
  <xs:element name="GetPersonByPartyNumberResponse" type="GetPersonByPartyNumberResponseType" />
  
  <!-- Root Type with polymorphic structure -->
  <xs:complexType name="GetPersonByPartyNumberResponseType">
    <xs:sequence>
      <!-- Always present: discriminator field -->
      <xs:element name="status" type="StatusType" minOccurs="1" maxOccurs="1" />
      <!-- Data on success (minOccurs=0 because it's absent on FAILED) -->
      <xs:element name="person" type="PersonResponseType" minOccurs="0" maxOccurs="1" />
      <!-- Errors on failure (unbounded array → JSON array) -->
      <xs:element name="errors" type="ErrorItemType" minOccurs="0" maxOccurs="unbounded" />
    </xs:sequence>
  </xs:complexType>
  
  <!-- Status values -->
  <xs:simpleType name="StatusType">
    <xs:restriction base="xs:string">
      <xs:enumeration value="SUCCESS" />
      <xs:enumeration value="FAILED" />
    </xs:restriction>
  </xs:simpleType>
  
  <!-- Error structure -->
  <xs:complexType name="ErrorItemType">
    <xs:sequence>
      <xs:element name="code" type="xs:string" minOccurs="1" maxOccurs="1" />
      <xs:element name="message" type="xs:string" minOccurs="1" maxOccurs="1" />
      <xs:element name="details" type="ErrorDetailsType" minOccurs="0" maxOccurs="1" />
    </xs:sequence>
  </xs:complexType>
  
  <!-- Data type with all response fields -->
  <xs:complexType name="PersonResponseType">
    <xs:sequence>
      <xs:element name="partyNumber" type="xs:string" minOccurs="1" maxOccurs="1" />
      <xs:element name="firstName" type="xs:string" minOccurs="1" maxOccurs="1" />
      <xs:element name="lastName" type="xs:string" minOccurs="1" maxOccurs="1" />
      <xs:element name="birthDate" type="xs:string" minOccurs="0" maxOccurs="1" />
      <!-- ... more fields -->
    </xs:sequence>
  </xs:complexType>
  
</xs:schema>
```

### Request XSD Structure

Request XSDs are **plain** (no status envelope) — just the input data structure:

```xml
<?xml version='1.0' encoding='utf-8'?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="unqualified">
  
  <!-- Root Element -->
  <xs:element name="CreateItemRequest" type="CreateItemRequestType" />
  
  <!-- Root Type with request fields -->
  <xs:complexType name="CreateItemRequestType">
    <xs:sequence>
      <!-- Item name (required) -->
      <xs:element name="name" type="xs:string" minOccurs="1" maxOccurs="1" />
      <!-- Item description (optional) -->
      <xs:element name="description" type="xs:string" minOccurs="0" maxOccurs="1" />
      <!-- Price (required) -->
      <xs:element name="price" type="xs:decimal" minOccurs="1" maxOccurs="1" />
    </xs:sequence>
  </xs:complexType>
  
</xs:schema>
```

### Key XSD Attributes Explained

| Attribute | Values | Meaning | Example |
|-----------|--------|---------|---------|
| `minOccurs` | `0` or `1` | Is this field optional? `0`=optional, `1`=required | `minOccurs="1"` = field must be present |
| `maxOccurs` | `1`, `unbounded` | Can this field appear multiple times? | `maxOccurs="unbounded"` = array (unlimited items) |
| `type` | XSD type name | Data type reference | `type="xs:string"` or `type="PersonResponseType"` |
| `name` | XML element name | Field name in XML | `name="firstName"` |

---

## Type Mapping Reference

### Automatic Type Conversion

The tool automatically converts JSON Schema types to XSD types:

| JSON Schema | OpenAPI Format | XSD Type | Example Values | Min/Max |
|-------------|---|----------|---|---|
| `string` | (none) | `xs:string` | "John", "Berlin" | Any text |
| `string` | `date` | `xs:string` | "2023-12-25" | ISO 8601 |
| `string` | `date-time` | `xs:string` | "2023-12-25T14:30:00Z" | ISO 8601 |
| `string` | `email` | `xs:string` | "user@example.com" | Email format |
| `string` | `uuid` | `xs:string` | "550e8400-e29b-41d4-a716-446655440000" | UUID format |
| `integer` | `int32` | `xs:int` | 42, -100 | -2,147,483,648 to 2,147,483,647 |
| `integer` | `int64` | `xs:long` | 9223372036854775807 | Very large integers |
| `number` | (decimal) | `xs:decimal` | 19.99, -0.50 | Precise decimals |
| `boolean` | (none) | `xs:boolean` | true, false | Binary |
| `object` | (none) | `xs:complexType` | {nested structure} | Nested object |
| `array` | (none) | `maxOccurs="unbounded"` | [item1, item2, ...] | Multiple occurrences |

---

## Real-World Examples

### Example 1: Complete GET Operation

**OpenAPI Specification:**
```json
{
  "paths": {
    "/v1/persons/{partyNumber}": {
      "get": {
        "operationId": "getPersonByPartyNumber",
        "description": "Retrieves person data from MAGDA by party number",
        "parameters": [
          {
            "name": "partyNumber",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "pattern": "^KSZ:\\d{11}$"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/PersonResponse" }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "PersonResponse": {
        "type": "object",
        "required": ["status"],
        "properties": {
          "status": {
            "type": "string",
            "enum": ["SUCCESS", "FAILED"],
            "description": "Operation outcome"
          },
          "person": {
            "type": "object",
            "description": "Person details (populated on success)",
            "properties": {
              "firstName": {
                "type": "string",
                "description": "Given name(s)"
              },
              "lastName": {
                "type": "string",
                "description": "Family name(s)"
              },
              "birthDate": {
                "type": "string",
                "format": "date",
                "description": "Date of birth (YYYY-MM-DD)"
              }
            },
            "required": ["firstName", "lastName"]
          },
          "errors": {
            "type": "array",
            "description": "Error list (populated on failure)",
            "items": {
              "type": "object",
              "properties": {
                "code": { "type": "string", "description": "Error code" },
                "message": { "type": "string", "description": "Error description" }
              },
              "required": ["code", "message"]
            }
          }
        }
      }
    }
  }
}
```

**Generated Response XSD:**
```xml
<?xml version='1.0' encoding='utf-8'?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="unqualified">
  <xs:element name="GetPersonByPartyNumberResponse" type="GetPersonByPartyNumberResponseType" />
  
  <xs:complexType name="GetPersonByPartyNumberResponseType">
    <xs:sequence>
      <!-- Always present: SUCCESS or FAILED -->
      <xs:element name="status" type="StatusType" minOccurs="1" maxOccurs="1" />
      <!-- Person details (populated on success) -->
      <xs:element name="person" type="PersonType" minOccurs="0" maxOccurs="1" />
      <!-- Error list (populated on failure) -->
      <xs:element name="errors" type="ErrorItemType" minOccurs="0" maxOccurs="unbounded" />
    </xs:sequence>
  </xs:complexType>
  
  <xs:simpleType name="StatusType">
    <xs:restriction base="xs:string">
      <xs:enumeration value="SUCCESS" />
      <xs:enumeration value="FAILED" />
    </xs:restriction>
  </xs:simpleType>
  
  <xs:complexType name="PersonType">
    <xs:sequence>
      <!-- Given name(s) -->
      <xs:element name="firstName" type="xs:string" minOccurs="1" maxOccurs="1" />
      <!-- Family name(s) -->
      <xs:element name="lastName" type="xs:string" minOccurs="1" maxOccurs="1" />
      <!-- Date of birth (YYYY-MM-DD) -->
      <xs:element name="birthDate" type="xs:string" minOccurs="0" maxOccurs="1" />
    </xs:sequence>
  </xs:complexType>
  
  <xs:complexType name="ErrorItemType">
    <xs:sequence>
      <!-- Error code -->
      <xs:element name="code" type="xs:string" minOccurs="1" maxOccurs="1" />
      <!-- Error description -->
      <xs:element name="message" type="xs:string" minOccurs="1" maxOccurs="1" />
    </xs:sequence>
  </xs:complexType>
  
</xs:schema>
```

**Command to Generate:**
```bash
python3 oic_xsd_gen.py path/to/openapi-spec.json
```

**Files Generated:**
- `generated/*/schemas/response/get-person-by-party-number-response.xsd` ← Upload to OIC
- `generated/*/schemas/json/get-person-by-party-number-response.schema.json` ← Reference only

---

### Example 2: Complete POST Operation (with Request)

**OpenAPI:**
```json
{
  "paths": {
    "/items": {
      "post": {
        "operationId": "createItem",
        "description": "Create a new inventory item",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/CreateItemRequest" }
            }
          }
        },
        "responses": {
          "201": {
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ItemResponse" }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "CreateItemRequest": {
        "type": "object",
        "required": ["name", "price"],
        "properties": {
          "name": {
            "type": "string",
            "description": "Item name (must be unique)"
          },
          "description": {
            "type": "string",
            "description": "Optional item description"
          },
          "price": {
            "type": "number",
            "description": "Unit price in EUR"
          },
          "category": {
            "type": "string",
            "enum": ["ELECTRONICS", "CLOTHING", "FOOD"],
            "description": "Product category"
          }
        }
      },
      "ItemResponse": {
        "type": "object",
        "required": ["status"],
        "properties": {
          "status": {
            "type": "string",
            "enum": ["SUCCESS", "FAILED"]
          },
          "item": {
            "type": "object",
            "properties": {
              "itemId": { "type": "string", "description": "Unique item ID" },
              "name": { "type": "string" },
              "price": { "type": "number" },
              "category": { "type": "string", "enum": ["ELECTRONICS", "CLOTHING", "FOOD"] },
              "createdAt": { "type": "string", "format": "date-time" }
            },
            "required": ["itemId", "name", "price"]
          },
          "errors": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "code": { "type": "string" },
                "message": { "type": "string" }
              }
            }
          }
        }
      }
    }
  }
}
```

**Generated Request XSD:**
```xml
<?xml version='1.0' encoding='utf-8'?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="unqualified">
  <xs:element name="CreateItemRequest" type="CreateItemRequestType" />
  
  <xs:complexType name="CreateItemRequestType">
    <xs:sequence>
      <!-- Item name (must be unique) -->
      <xs:element name="name" type="xs:string" minOccurs="1" maxOccurs="1" />
      <!-- Optional item description -->
      <xs:element name="description" type="xs:string" minOccurs="0" maxOccurs="1" />
      <!-- Unit price in EUR -->
      <xs:element name="price" type="xs:decimal" minOccurs="1" maxOccurs="1" />
      <!-- Product category -->
      <xs:element name="category" type="CategoryType" minOccurs="0" maxOccurs="1" />
    </xs:sequence>
  </xs:complexType>
  
  <xs:simpleType name="CategoryType">
    <xs:restriction base="xs:string">
      <xs:enumeration value="ELECTRONICS" />
      <xs:enumeration value="CLOTHING" />
      <xs:enumeration value="FOOD" />
    </xs:restriction>
  </xs:simpleType>
  
</xs:schema>
```

**Generated Response XSD:**
```xml
<?xml version='1.0' encoding='utf-8'?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="unqualified">
  <xs:element name="CreateItemResponse" type="CreateItemResponseType" />
  
  <xs:complexType name="CreateItemResponseType">
    <xs:sequence>
      <xs:element name="status" type="StatusType" minOccurs="1" maxOccurs="1" />
      <!-- Item details (populated on success) -->
      <xs:element name="item" type="ItemType" minOccurs="0" maxOccurs="1" />
      <!-- Error details (populated on failure) -->
      <xs:element name="errors" type="ErrorItemType" minOccurs="0" maxOccurs="unbounded" />
    </xs:sequence>
  </xs:complexType>
  
  <xs:simpleType name="StatusType">
    <xs:restriction base="xs:string">
      <xs:enumeration value="SUCCESS" />
      <xs:enumeration value="FAILED" />
    </xs:restriction>
  </xs:simpleType>
  
  <xs:complexType name="ItemType">
    <xs:sequence>
      <!-- Unique item ID -->
      <xs:element name="itemId" type="xs:string" minOccurs="1" maxOccurs="1" />
      <xs:element name="name" type="xs:string" minOccurs="1" maxOccurs="1" />
      <xs:element name="price" type="xs:decimal" minOccurs="1" maxOccurs="1" />
      <xs:element name="category" type="CategoryType" minOccurs="0" maxOccurs="1" />
      <xs:element name="createdAt" type="xs:string" minOccurs="0" maxOccurs="1" />
    </xs:sequence>
  </xs:complexType>
  
  <xs:complexType name="ErrorItemType">
    <xs:sequence>
      <xs:element name="code" type="xs:string" minOccurs="1" maxOccurs="1" />
      <xs:element name="message" type="xs:string" minOccurs="1" maxOccurs="1" />
    </xs:sequence>
  </xs:complexType>
  
</xs:schema>
```

**Files Generated:**
- `generated/*/schemas/request/create-item-request.xsd` ← Optional: Upload for request validation
- `generated/*/schemas/response/create-item-response.xsd` ← Required: Upload as response schema

---

## Integration with OIC Gen3

### Step-by-Step Integration

#### 1. Generate XSD Files

```bash
python3 oic_xsd_gen.py /path/to/openapi-spec.json -o ./schemas
```

Verify the output:
```bash
ls -la schemas/
# Should see: request/, response/, json/ directories
```

#### 2. Access OIC Console

1. Navigate to your OIC Gen3 instance: `https://{your-oic-instance}.oic.oraclecloud.com/`
2. Login with your OIC credentials
3. Click **Home** → **Integrations**

#### 3. Create New Integration

**Option A: Create New**
1. Click **Create** button
2. Select **App Driven Orchestration**
3. Enter integration details:
   - **Name:** (e.g., `I038_INB_PARTIJHUB_MAGDA_GETPERSON`)
   - **Description:** Clear description including source/target systems
   - **Identifier:** Auto-generated (e.g., `I038`)
   - **Version:** 01.00.0000
4. Click **Create**

**Option B: Edit Existing**
1. Find integration in list
2. Click **Edit** (three dots menu)
3. Modify as needed

#### 4. Add REST Adapter Trigger

1. In the integration canvas, click **Add Trigger**
2. Select **REST Adapter**
3. Configure trigger:
   - **Connection:** (Select or create REST connection)
   - **Trigger Name:** (e.g., `GetPersonByPartyNumber_Trigger`)
   - **Relative Resource URI:** `/persons/{partyNumber}`
   - **HTTP Method:** GET (or POST, PUT, etc.)

#### 5. Configure Response Payload (XML Schema)

**This is the most critical step for XSD integration.**

1. In REST trigger configuration, navigate to **Response** section
2. Click **Add** next to Response Payload
3. **Response Payload Type:** Select **XML**
4. **Response Payload:**
   - Click **Upload** button
   - Select the **response XSD file** from `schemas/response/get-person-by-party-number-response.xsd`
   - File uploads and displays in the editor
5. **Root Element:** 
   - Dropdown appears with available root elements
   - Select `GetPersonByPartyNumberResponse` (or your operation name + "Response")
   - Click **OK**
6. Verify the schema is loaded (should show element structure in the tree)

#### 6. Configure Request Payload (XML Schema) - If POST/PUT/PATCH

**Only for operations with request bodies:**

1. Navigate to **Request** section
2. Click **Add** next to Request Payload
3. **Request Payload Type:** Select **XML**
4. **Request Payload:**
   - Click **Upload** button
   - Select the **request XSD file** from `schemas/request/create-item-request.xsd`
5. **Root Element:** Select the root element (e.g., `CreateItemRequest`)
6. Click **OK**

#### 7. Add Integration Logic

1. In the integration canvas, click **+** to add an invoke action
2. Configure the backend system call (e.g., invoke MAGDA service)
3. Map the request:
   - OIC automatically parses the incoming XML using the request XSD
   - Available fields shown in mapping panel
4. Handle the response:
   - Map backend response to the response XSD structure
   - **Success path:** Create XML with status="SUCCESS" and populate data fields
   - **Fault handler:** Create XML with status="FAILED" and populate errors array

**Example Success Mapping:**
```xml
<!-- Generated by mapping logic -->
<GetPersonByPartyNumberResponse>
  <status>SUCCESS</status>
  <person>
    <partyNumber>KSZ:80010120990</partyNumber>
    <firstName>John</firstName>
    <lastName>Doe</lastName>
    <birthDate>1980-01-12</birthDate>
  </person>
</GetPersonByPartyNumberResponse>
```

**Example Error Mapping:**
```xml
<!-- Generated by fault handler -->
<GetPersonByPartyNumberResponse>
  <status>FAILED</status>
  <errors>
    <code>PERSON_NOT_FOUND</code>
    <message>No person record found for KSZ:80010120990</message>
    <details>
      <identification>MAGDA_ERROR_12345</identification>
      <diagnose>Query timeout after 30 seconds</diagnose>
    </details>
  </errors>
</GetPersonByPartyNumberResponse>
```

#### 8. Test the Integration

1. Click **Test** button in OIC console
2. For **GET request:**
   - Enter path parameter (e.g., `partyNumber=KSZ:80010120990`)
   - Click **Send Request**
   - Verify response contains valid XML matching the response XSD
3. For **POST request:**
   - Provide request body matching the request XSD
   - Click **Send Request**
   - Verify response
4. Test error scenarios:
   - Invalid input (missing required fields)
   - Backend service errors
   - Verify error response matches XSD structure

#### 9. Save and Activate Integration

1. Click **Save** (Ctrl+S)
2. Click **Activate** button
3. Confirm activation (integrations become live)
4. Note the integration endpoint URL (shown after activation)

#### 10. Expose via API Gateway (Optional)

For external API access with OAuth2:

1. Navigate to **API Gateway**
2. Click **Create API** → **From Integrations**
3. Select your integration from the list
4. Configure:
   - **Resource Path:** `/api/v1/persons`
   - **Methods:** GET (matching your operation)
   - **Security Policies:** OAuth2, rate limiting, etc.
5. Deploy API
6. Share API endpoint with consumers

#### 11. Monitor & Troubleshoot

1. In OIC console, click **Monitoring** → **Integrations**
2. Click on your integration to view:
   - **Execution traces:** See what happened
   - **Errors:** Check for validation issues
   - **Audit trail:** See who accessed/modified integration
3. Check logs for:
   - XML validation errors
   - Schema mismatch issues
   - Backend service errors

---

## OIC Gen3 Error Handling

### Standard Error Response Format

All errors must follow this format (generated from your response XSD):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GetPersonByPartyNumberResponse>
  <status>FAILED</status>
  <errors>
    <code>ERROR_CODE_1</code>
    <message>Descriptive error message for client</message>
    <details>
      <identification>SYSTEM_ERROR_ID_12345</identification>
      <diagnose>Technical details for troubleshooting</diagnose>
    </details>
  </errors>
</GetPersonByPartyNumberResponse>
```

### Common Error Codes

Define these in your OpenAPI spec and handle in OIC mapping:

| Error Code | HTTP Status | Meaning | Action |
|------------|-------------|---------|--------|
| `INVALID_INPUT` | 400 | Missing/invalid required fields | Validate input before sending |
| `INVALID_REQUEST_FORMAT` | 400 | Request doesn't match XSD | Check XML structure |
| `UNAUTHORIZED` | 401 | No/invalid credentials | Provide auth token |
| `FORBIDDEN` | 403 | User lacks permissions | Request elevated access |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist | Verify resource ID |
| `CONFLICT` | 409 | Data conflict (e.g., duplicate) | Resolve conflict before retry |
| `INTERNAL_SERVER_ERROR` | 500 | Backend service error | Contact support |
| `SERVICE_UNAVAILABLE` | 503 | Backend service down | Retry after delay |
| `TIMEOUT` | 504 | Request took too long | Increase timeout, retry |

### OIC Mapping for Error Handling

In OIC integration, create a fault handler:

```
Error Handler (catches exceptions from backend call):
  1. Capture error code and message
  2. Map to error response structure:
     status = "FAILED"
     errors[0].code = "PERSON_NOT_FOUND" (if not found)
     errors[0].message = "No person found for {partyNumber}"
     errors[0].details.identification = "MAGDA_ERROR_..." (backend error ID)
     errors[0].details.diagnose = "..." (backend error details)
  3. Return mapped error XML (OIC automatically converts to JSON for client)
```

### Response Type Conversions

OIC automatically handles these conversions:

| OIC Internal | REST Trigger | Client Receives |
|------------|--------------|-----------------|
| XML (validated by XSD) | Response Payload Type = XML | JSON (auto-converted) |
| JSON variables | Mapped to XML elements | JSON (from XML) |
| Complex nested object | Nested XML elements | Nested JSON object |
| Array values | `maxOccurs="unbounded"` | JSON array `[]` |

**Example:**

Your XSD:
```xml
<xs:element name="errors" type="ErrorItemType" minOccurs="0" maxOccurs="unbounded" />
```

OIC generates:
```xml
<GetPersonByPartyNumberResponse>
  <status>FAILED</status>
  <errors>
    <code>PERSON_NOT_FOUND</code>
    <message>Person not found</message>
  </errors>
  <errors>
    <code>INVALID_FORMAT</code>
    <message>Party number invalid</message>
  </errors>
</GetPersonByPartyNumberResponse>
```

Client receives (auto-converted):
```json
{
  "status": "FAILED",
  "errors": [
    {
      "code": "PERSON_NOT_FOUND",
      "message": "Person not found"
    },
    {
      "code": "INVALID_FORMAT",
      "message": "Party number invalid"
    }
  ]
}
```

---

## XSD to OIC Type Mapping

When OIC loads your XSD, it automatically understands these types:

| XSD Type | OIC Type | JSON Equivalent | Example |
|----------|----------|----------------|---------|
| `xs:string` | String | string | "John Doe" |
| `xs:int` | Integer | number | 42 |
| `xs:long` | Long | number | 9223372036854775807 |
| `xs:decimal` | Decimal | number | 19.99 |
| `xs:boolean` | Boolean | boolean | true / false |
| `xs:dateTime` | Timestamp | string | "2024-03-15T14:30:00Z" |
| `xs:complexType` | Object/Element | object | { nested fields } |
| `maxOccurs="unbounded"` | Array | array | [item1, item2] |

---

## Troubleshooting Guide

### Issue: "Missing operationId"

**Error Message:**
```
Skipped operations:
- unknown operation (GET /v1/persons/{partyNumber})
  Reason: Missing operationId
```

**Solution:**
Add `operationId` to your OpenAPI operation:
```json
{
  "paths": {
    "/v1/persons/{partyNumber}": {
      "get": {
        "operationId": "getPersonByPartyNumber",  ← Add this line
        "description": "..."
      }
    }
  }
}
```

---

### Issue: "No 200 or 201 success response found"

**Error Message:**
```
Skipped operations:
- createItem (POST /items)
  Reason: No 200 or 201 success response found
```

**Solution:**
Define a success response in your OpenAPI:
```json
{
  "responses": {
    "201": {  ← Use 200 for GET/PUT/PATCH, 201 for POST
      "description": "Item created",
      "content": {
        "application/json": {
          "schema": { "$ref": "#/components/schemas/ItemResponse" }
        }
      }
    }
  }
}
```

---

### Issue: "No application/json schema found on success response"

**Error Message:**
```
Skipped operations:
- getItems (GET /items)
  Reason: No application/json schema found on success response
```

**Solution:**
Ensure your response includes `application/json` content type:
```json
{
  "responses": {
    "200": {
      "description": "Success",
      "content": {
        "application/json": {  ← Must be present
          "schema": { "$ref": "#/components/schemas/ItemList" }
        }
      }
    }
  }
}
```

---

### Issue: "Could not detect the data property"

**Error Message:**
```
Skipped operations:
- getItems (GET /items)
  Reason: Could not detect the data property. Expected success envelope like { status, person } or { status, enterprise }.
```

**Solution:**
Ensure your response schema has `status` and at least one data property (not just `status` and `errors`):
```json
{
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": { "type": "string", "enum": ["SUCCESS", "FAILED"] },
    "items": {  ← Data property required
      "type": "array",
      "items": { "type": "object" }
    },
    "errors": { "type": "array" }
  }
}
```

---

### Issue: "Object of type dict is not JSON serializable"

**Error Message:**
```
Failed: Object of type dict is not JSON serializable
```

**Solution:**
This usually occurs with complex `$ref` resolution. Ensure your OpenAPI file is valid JSON/YAML and all references are resolvable:
```bash
# Validate JSON
python3 -m json.tool /path/to/spec.json > /dev/null

# Or for YAML
python3 -c "import yaml; yaml.safe_load(open('/path/to/spec.yaml'))"
```

---

### Issue: "Object of type dict is not JSON serializable"

**Error Message:**
```
Failed: Object of type dict is not JSON serializable
```

**Solution:**
This usually occurs with complex `$ref` resolution. Ensure your OpenAPI file is valid JSON/YAML and all references are resolvable:
```bash
# Validate JSON
python3 -m json.tool /path/to/spec.json > /dev/null

# Or for YAML
python3 -c "import yaml; yaml.safe_load(open('/path/to/spec.yaml'))"
```

---

### Error Handling in OpenAPI

Define comprehensive error responses in your OpenAPI:

```json
{
  "responses": {
    "200": {
      "description": "Success",
      "content": {
        "application/json": {
          "schema": { "$ref": "#/components/schemas/SuccessResponse" }
        }
      }
    },
    "400": {
      "description": "Bad request - Invalid input",
      "content": {
        "application/json": {
          "schema": { "$ref": "#/components/schemas/ErrorResponse" }
        }
      }
    },
    "401": {
      "description": "Unauthorized - Invalid credentials",
      "content": {
        "application/json": {
          "schema": { "$ref": "#/components/schemas/ErrorResponse" }
        }
      }
    },
    "403": {
      "description": "Forbidden - Insufficient permissions",
      "content": {
        "application/json": {
          "schema": { "$ref": "#/components/schemas/ErrorResponse" }
        }
      }
    },
    "404": {
      "description": "Not found - Resource doesn't exist",
      "content": {
        "application/json": {
          "schema": { "$ref": "#/components/schemas/ErrorResponse" }
        }
      }
    },
    "500": {
      "description": "Internal server error",
      "content": {
        "application/json": {
          "schema": { "$ref": "#/components/schemas/ErrorResponse" }
        }
      }
    }
  }
}
```

All error responses must use the same **ErrorResponse** schema with the polymorphic envelope (status="FAILED").

---

### Logging Generated Schemas

Enable logging when generating schemas:

```python
import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schema-generation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def generate_schema(openapi_file, output_dir):
    try:
        logger.info(f"Starting generation for {openapi_file}")
        result = subprocess.run(
            ["python3", "oic_xsd_gen.py", openapi_file, "-o", output_dir],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✓ Successfully generated schemas for {openapi_file}")
        else:
            logger.error(f"✗ Failed to generate schemas: {result.stderr}")
    
    except Exception as e:
        logger.exception(f"Exception during schema generation: {e}")
```

---

### Advanced Troubleshooting

### 1. Document Everything in OpenAPI

Add comprehensive descriptions to every property and operation:

```json
{
  "operationId": "getPersonByPartyNumber",
  "description": "Retrieves person data from MAGDA (Belgian citizen registry). The partyNumber must follow the format KSZ:INSZ where INSZ is an 11-digit Belgian identification number.",
  "parameters": [
    {
      "name": "partyNumber",
      "in": "path",
      "required": true,
      "description": "Oracle party number in format 'KSZ:{11-digit-INSZ}'. Example: KSZ:80010120990",
      "schema": { "type": "string", "pattern": "^KSZ:\\d{11}$" }
    }
  ]
}
```

### 2. Use Version Control

Keep both OpenAPI spec and generated XSD in source control:

```
apis/
├── partijhub/
│   ├── spec/
│   │   └── partijhub-api-v1.0.0.json  ← Source of truth
│   └── schemas/
│       ├── response/
│       │   └── get-person-by-party-number-response.xsd  ← Generated, version controlled
│       └── request/
│           └── (request XSDs if applicable)
```

Commit both files together so they stay in sync.

### 3. Regenerate After OpenAPI Changes

Whenever you update the OpenAPI spec, regenerate the XSD:

```bash
# After updating openapi-spec.json
python3 oic_xsd_gen.py apis/partijhub/spec/partijhub-api-v1.0.0.json

# Review changes
git diff generated/

# Commit together
git add apis/partijhub/spec/partijhub-api-v1.0.0.json generated/...
git commit -m "Update partijhub API spec and regenerate XSD schemas"
```

### 4. Use Meaningful Enum Values

In OpenAPI enums, use values that are clear and maintainable:

```json
{
  "status": {
    "type": "string",
    "enum": ["01", "02"],
    "description": "Register type: 01 = Rijksregister (official), 02 = BIS (alternative)"
  }
}
```

Generated XSD includes the description as a comment:
```xml
<!-- Register type: 01 = Rijksregister (official), 02 = BIS (alternative) -->
<xs:element name="status" type="RegisterStatusType" />
```

### 5. Validate Generated XSD Files

Before uploading to OIC, validate the XSD using multiple methods:

**Method 1: Python Validation**
```bash
python3 -c "
from xml.etree import ElementTree as ET
try:
    ET.parse('generated/*/schemas/response/get-person-response.xsd')
    print('✓ XSD is well-formed XML')
except ET.ParseError as e:
    print(f'✗ XSD XML error: {e}')
"
```

**Method 2: XSD Schema Validation**
```python
#!/usr/bin/env python3
import sys
from xml.etree import ElementTree as ET

def validate_xsd(xsd_file):
    """Validate XSD file structure"""
    try:
        tree = ET.parse(xsd_file)
        root = tree.getroot()
        
        # Check for required namespace
        if 'http://www.w3.org/2001/XMLSchema' not in root.tag:
            print(f"✗ Missing XML Schema namespace")
            return False
        
        # Check for root element
        elements = root.findall('{http://www.w3.org/2001/XMLSchema}element')
        if not elements:
            print(f"✗ No xs:element found")
            return False
        
        print(f"✓ XSD is valid")
        print(f"  - Root element: {elements[0].get('name')}")
        print(f"  - Type: {elements[0].get('type')}")
        return True
    
    except ET.ParseError as e:
        print(f"✗ XSD Parse Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Validation Error: {e}")
        return False

if __name__ == "__main__":
    xsd_file = sys.argv[1]
    success = validate_xsd(xsd_file)
    sys.exit(0 if success else 1)
```

Usage:
```bash
python3 validate-xsd.py generated/*/schemas/response/get-person-response.xsd
```

**Method 3: Validate Sample XML Against XSD**
```python
#!/usr/bin/env python3
from lxml import etree
import sys

def validate_xml_against_xsd(xml_file, xsd_file):
    """Validate XML instance against XSD schema"""
    try:
        # Parse XSD
        with open(xsd_file, 'r') as f:
            xsd_doc = etree.parse(f)
            xsd_schema = etree.XMLSchema(xsd_doc)
        
        # Parse XML
        with open(xml_file, 'r') as f:
            xml_doc = etree.parse(f)
        
        # Validate
        if xsd_schema.validate(xml_doc):
            print(f"✓ XML is valid against XSD")
            return True
        else:
            print(f"✗ XML validation errors:")
            for error in xsd_schema.error_log:
                print(f"  Line {error.lineno}: {error.message}")
            return False
    
    except Exception as e:
        print(f"✗ Validation Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 validate-xml.py <xml-file> <xsd-file>")
        sys.exit(1)
    
    success = validate_xml_against_xsd(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
```

Usage:
```bash
python3 validate-xml.py sample-success.xml generated/*/schemas/response/get-person-response.xsd
python3 validate-xml.py sample-error.xml generated/*/schemas/response/get-person-response.xsd
```

**Method 4: Online Validators**
- [FreeFormatter XSD/XML Validator](https://www.freeformatter.com/xml-validator-xsd.html)
- [W3C XML Schema Validator](https://www.w3.org/XML/Schema)

**Method 5: IDE Validation**
- Open XSD in VS Code with XML extension
- Look for red squiggly lines (errors)
- Check Problems panel for validation issues

### 6. Document API Contract Changes

When you change the OpenAPI spec, document the impact:

```
## API Changes (v1.0.1)

- Added `middleName` field to PersonResponse (optional)
- Added `deathDate` field to PersonResponse (optional)
- Changed `status` enum values: now ["SUCCESS", "FAILED"] (was ["OK", "ERROR"])

Action: Regenerate XSD and redeploy OIC integrations
Impact: Backward compatible for existing clients
```

### 7. Test Both Paths

Create test cases for success and failure paths:

**Success (status="SUCCESS"):**
```json
{
  "status": "SUCCESS",
  "person": {
    "firstName": "John",
    "lastName": "Doe"
  }
}
```

**Failure (status="FAILED"):**
```json
{
  "status": "FAILED",
  "errors": [
    {
      "code": "PERSON_NOT_FOUND",
      "message": "No person found for KSZ:80010120990"
    }
  ]
}
```

---

## Testing the Tool

### Test 1: GET-Only API

```bash
python3 oic_xsd_gen.py test-input/partijhub-api-v1.0.0.json

# Expected output:
# Generated files:
# - getPersonByPartyNumber (GET /v1/persons/{partyNumber})
#   Response XSD: ./generated/.../get-person-by-party-number-response.xsd
```

**Verify:**
- Response XSD exists and is valid ✓
- No request XSD generated (as expected for GET) ✓
- Comments included from OpenAPI descriptions ✓

### Test 2: POST API with Request & Response

```bash
python3 oic_xsd_gen.py test-input/sample-api-v1.0.0.json

# Expected output:
# Generated files:
# - createItem (POST /items)
#   Response XSD: ./generated/.../create-item-response.xsd
#   Request XSD:  ./generated/.../create-item-request.xsd
# - getItemById (GET /items/{itemId})
#   Response XSD: ./generated/.../get-item-by-id-response.xsd
```

**Verify:**
- Response XSD exists ✓
- Request XSD generated for POST ✓
- Request XSD NOT generated for GET ✓
- Both files are valid XML/XSD ✓

### Test 3: Custom Output Directory

```bash
python3 oic_xsd_gen.py test-input/sample-api-v1.0.0.json -o ./my-schemas

# Verify files exist in ./my-schemas/
ls -la my-schemas/
```

---

## Batch Processing & Automation

### Batch Generate Multiple APIs

For government systems managing multiple integrations, automate schema generation:

**Bash Script Example:**

```bash
#!/bin/bash
# batch-generate-schemas.sh
# Purpose: Generate XSD schemas for all OpenAPI specs in the apis/ directory

set -e  # Exit on error

APIS_DIR="./apis"
OUTPUT_DIR="./generated"
LOG_FILE="./generation-$(date +%Y%m%d-%H%M%S).log"

echo "=== Batch Schema Generation Started ===" | tee $LOG_FILE
echo "Timestamp: $(date)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

TOTAL=0
SUCCESS=0
FAILED=0

for api_dir in $APIS_DIR/*/; do
    for spec_file in "$api_dir"spec/*.json "$api_dir"spec/*.yaml; do
        if [ -f "$spec_file" ]; then
            TOTAL=$((TOTAL + 1))
            API_NAME=$(basename "$api_dir")
            SPEC_NAME=$(basename "$spec_file")
            
            echo "Processing: $API_NAME/$SPEC_NAME" | tee -a $LOG_FILE
            
            if python3 oic_xsd_gen.py "$spec_file" -o "$OUTPUT_DIR/$API_NAME"; then
                echo "✓ SUCCESS: Generated schemas for $SPEC_NAME" | tee -a $LOG_FILE
                SUCCESS=$((SUCCESS + 1))
            else
                echo "✗ FAILED: Could not generate schemas for $SPEC_NAME" | tee -a $LOG_FILE
                FAILED=$((FAILED + 1))
            fi
            echo "" | tee -a $LOG_FILE
        fi
    done
done

echo "=== Batch Generation Complete ===" | tee -a $LOG_FILE
echo "Total APIs: $TOTAL" | tee -a $LOG_FILE
echo "Successful: $SUCCESS" | tee -a $LOG_FILE
echo "Failed: $FAILED" | tee -a $LOG_FILE
echo "Log saved to: $LOG_FILE" | tee -a $LOG_FILE
```

**Usage:**
```bash
chmod +x batch-generate-schemas.sh
./batch-generate-schemas.sh
```

### Python Batch Script

For more complex automation with Python:

```python
#!/usr/bin/env python3
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

def batch_generate(apis_dir="./apis", output_dir="./generated"):
    """Generate XSD schemas for all OpenAPI specs"""
    
    stats = {"total": 0, "success": 0, "failed": 0, "errors": []}
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = f"generation-{timestamp}.log"
    
    with open(log_file, "w") as log:
        log.write("=== Batch Schema Generation Started ===\n")
        log.write(f"Timestamp: {datetime.now()}\n\n")
        
        for api_dir in Path(apis_dir).iterdir():
            if not api_dir.is_dir():
                continue
            
            spec_dir = api_dir / "spec"
            if not spec_dir.exists():
                continue
            
            for spec_file in spec_dir.glob("*.json") + spec_dir.glob("*.yaml"):
                stats["total"] += 1
                api_name = api_dir.name
                spec_name = spec_file.name
                output_path = os.path.join(output_dir, api_name)
                
                print(f"Processing: {api_name}/{spec_name}")
                log.write(f"Processing: {api_name}/{spec_name}\n")
                
                try:
                    result = subprocess.run(
                        ["python3", "oic_xsd_gen.py", str(spec_file), "-o", output_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        print(f"✓ SUCCESS: Generated schemas for {spec_name}")
                        log.write(f"✓ SUCCESS: Generated schemas for {spec_name}\n")
                        stats["success"] += 1
                    else:
                        print(f"✗ FAILED: {spec_name}")
                        log.write(f"✗ FAILED: {spec_name}\n")
                        log.write(f"  Error: {result.stderr}\n")
                        stats["failed"] += 1
                        stats["errors"].append(f"{api_name}/{spec_name}: {result.stderr}")
                
                except subprocess.TimeoutExpired:
                    print(f"✗ TIMEOUT: {spec_name}")
                    log.write(f"✗ TIMEOUT: {spec_name}\n")
                    stats["failed"] += 1
                    stats["errors"].append(f"{api_name}/{spec_name}: Timeout")
                
                except Exception as e:
                    print(f"✗ ERROR: {spec_name} - {str(e)}")
                    log.write(f"✗ ERROR: {spec_name} - {str(e)}\n")
                    stats["failed"] += 1
                    stats["errors"].append(f"{api_name}/{spec_name}: {str(e)}")
                
                log.write("\n")
        
        log.write("\n=== Batch Generation Complete ===\n")
        log.write(f"Total APIs: {stats['total']}\n")
        log.write(f"Successful: {stats['success']}\n")
        log.write(f"Failed: {stats['failed']}\n")
        if stats['errors']:
            log.write(f"\nErrors:\n")
            for error in stats['errors']:
                log.write(f"  - {error}\n")
    
    # Print summary
    print(f"\n=== Summary ===")
    print(f"Total: {stats['total']}")
    print(f"Success: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Log: {log_file}")
    
    return stats["failed"] == 0

if __name__ == "__main__":
    success = batch_generate()
    sys.exit(0 if success else 1)
```

### CI/CD Pipeline Integration

For government systems using CI/CD, add to your pipeline:

**GitHub Actions Example:**
```yaml
name: Generate XSD Schemas

on:
  push:
    paths:
      - 'apis/**/spec/*.json'
      - 'apis/**/spec/*.yaml'
      - '.github/workflows/generate-xsd.yml'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Generate schemas
        run: python3 batch-generate-schemas.py
      
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add generated/
          git commit -m "Auto-generated XSD schemas"
          git push
```

---

## Version History & Updates

### Current Version
- ✅ Request XSD generation for POST/PUT/PATCH/DELETE
- ✅ Automatic comment extraction from OpenAPI descriptions
- ✅ Duplicate type deduplication
- ✅ Support for both JSON and YAML OpenAPI specs
- ✅ Reference resolution (`$ref` handling)

### Future Enhancements (Planned)
- Support for additional type formats (date, time, UUID, etc.)
- Batch processing multiple OpenAPI files
- Custom naming templates for types
- XSD annotation with additional metadata
- Integration with CI/CD pipelines
- Web UI for interactive generation

---

## Government-Specific Guidance

### Data Mapping & Audit Trail Requirements

In government systems, every data field must be traceable. Use the OpenAPI `description` field to document:
1. **Source system** (where data comes from)
2. **Target system** (where data goes)
3. **Data classification** (if applicable)
4. **Transformation logic** (if any)

**Best Practice Example:**

```json
{
  "firstName": {
    "type": "string",
    "description": "Individual's given name | Source: MAGDA (Person.FirstName) | Target: Oracle HCM (Person.PersonFirstName) | Classification: Public | Transformation: Uppercase converted to mixed case"
  },
  "identificationNumber": {
    "type": "string",
    "description": "Belgian INSZ number (11 digits) | Source: MAGDA (Person.INSZ) | Target: Oracle HCM (Person.PersonNationalIdentifier) | Classification: Sensitive PII | Transformation: None"
  },
  "administrativeStatus": {
    "type": "string",
    "enum": ["ACTIVE", "DECEASED", "DELETED"],
    "description": "Person status in government registry | Values: ACTIVE = current citizen, DECEASED = deceased (archive), DELETED = removed from system | Source: MAGDA (Person.Status) | Target: Oracle HCM (Status)"
  }
}
```

This generates XSD with embedded comments that serve as audit trail:

```xml
<!-- Individual's given name | Source: MAGDA (Person.FirstName) | Target: Oracle HCM (Person.PersonFirstName) | Classification: Public | Transformation: Uppercase converted to mixed case -->
<xs:element name="firstName" type="xs:string" minOccurs="1" maxOccurs="1" />
```

### Data Classification Standards

Document data sensitivity in descriptions:

```
Classification: [Public | Internal | Confidential | Restricted]
```

| Classification | Example | XSD Treatment |
|----------------|---------|---------------|
| **Public** | First name, last name | No special handling required |
| **Internal** | Employee number, department | Document in comments, standard XSD |
| **Confidential** | Social security number, medical data | Restrict access, log all accesses |
| **Restricted** | Genetic data, biometric data | Encrypt in transit/storage, audit all access |

### Version Management for Government

Create a formal versioning strategy:

**Version Naming:** `v{MAJOR}.{MINOR}.{PATCH}-{DATE}`

Example: `partijhub-api-v1.0.0-2024-03-15.json`

**CHANGELOG format:**
```markdown
## Version History

### v1.0.0 (2024-03-15)
- Initial release for production
- Operations: getPersonByPartyNumber (GET)
- Fields: partyNumber, firstName, lastName, birthDate, identificationNumber, nationality, registerType, administrativeStatus
- Error codes: PERSON_NOT_FOUND, INVALID_PARTY_NUMBER, MAGDA_TIMEOUT, MAGDA_ERROR
- Approved by: [Name], [Title], [Date]
- Deployment: [System name], [Environment]

### v1.0.1 (2024-04-10)
- Added middleName field (optional)
- Added deathDate field (optional)
- Updated registerType enum with documentation
- Breaking changes: None
- Backward compatible: Yes
- Approved by: [Name], [Title], [Date]
```

### Compliance Documentation

For government deployments, maintain:

1. **Data Dictionary**
   - Field names and types
   - Source/target system mappings
   - Data classification
   - Transformation rules

2. **Integration Flow Diagram**
   - OpenAPI → XSD → OIC integration
   - Source system → OIC → Target system
   - Error handling paths

3. **Validation Matrix**
   - Type validation (string, number, etc.)
   - Enum restrictions
   - Required/optional fields
   - Pattern validation (if any)

4. **Security & Access Control**
   - Who can modify the spec
   - Who approves changes
   - Who can view audit logs
   - Data access restrictions

---

## Advanced Troubleshooting

### Complex Scenarios

#### Scenario 1: Nested Objects with Multiple Levels

**Problem:** Your OpenAPI spec has deeply nested objects and the generated XSD is confusing.

**Solution:**
```json
{
  "type": "object",
  "properties": {
    "organization": {
      "type": "object",
      "description": "Organization hierarchy level 1",
      "properties": {
        "department": {
          "type": "object",
          "description": "Department hierarchy level 2",
          "properties": {
            "team": {
              "type": "object",
              "description": "Team hierarchy level 3",
              "properties": {
                "teamName": { "type": "string" },
                "memberCount": { "type": "integer" }
              }
            }
          }
        }
      }
    }
  }
}
```

**Generated XSD will have:**
- `OrganizationType` (root level)
- `DepartmentType` (nested)
- `TeamType` (nested further)
- Clear hierarchy with minOccurs/maxOccurs on each level

#### Scenario 2: Arrays of Complex Objects

**Problem:** You have arrays of objects with multiple fields and need to ensure they're properly represented.

**OpenAPI:**
```json
{
  "items": {
    "type": "array",
    "description": "List of transaction items",
    "items": {
      "type": "object",
      "required": ["transactionId", "amount"],
      "properties": {
        "transactionId": {
          "type": "string",
          "description": "Unique transaction identifier"
        },
        "amount": {
          "type": "number",
          "description": "Transaction amount in EUR"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time",
          "description": "When transaction occurred"
        }
      }
    }
  }
}
```

**Generated XSD:**
```xml
<!-- Multiple occurrences: unbounded -->
<xs:element name="items" type="TransactionItemType" minOccurs="0" maxOccurs="unbounded" />

<xs:complexType name="TransactionItemType">
  <xs:sequence>
    <xs:element name="transactionId" type="xs:string" minOccurs="1" maxOccurs="1" />
    <xs:element name="amount" type="xs:decimal" minOccurs="1" maxOccurs="1" />
    <xs:element name="timestamp" type="xs:string" minOccurs="0" maxOccurs="1" />
  </xs:sequence>
</xs:complexType>
```

#### Scenario 3: Handling Polymorphic Responses

**Problem:** Different status codes return different response structures.

**Solution:** Always use the single-envelope pattern:
```json
{
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["SUCCESS", "FAILED"],
      "description": "Operation result"
    },
    "successData": {
      "type": "object",
      "description": "Data when status=SUCCESS"
    },
    "errors": {
      "type": "array",
      "description": "Errors when status=FAILED"
    }
  }
}
```

This creates a **single XSD** that OIC Gen3 can use for both success and error responses.

---

## Compliance & Audit Trail

### Government Compliance Checklist

✅ **Documentation Standards**
- [ ] All operations have `operationId` (required for audit trail)
- [ ] All fields have `description` (required for governance)
- [ ] All enums documented with meaningful values
- [ ] Request/response structures match OpenAPI spec exactly

✅ **Data Integrity**
- [ ] XSD validates all request payloads (type checking)
- [ ] XSD enforces required/optional fields (minOccurs/maxOccurs)
- [ ] Enum restrictions prevent invalid values
- [ ] No duplicate type definitions

✅ **Audit Trail**
- [ ] OpenAPI spec in version control with commit history
- [ ] Generated XSD files committed alongside OpenAPI
- [ ] Version tags created for each release
- [ ] Change log maintained for all modifications

✅ **Compliance Requirements**
- [ ] All personal data fields clearly identified in descriptions
- [ ] Data classification documented (if applicable)
- [ ] Backend system mappings documented in field descriptions
- [ ] Error handling documented with error codes

### Version Control Strategy

**Recommended approach for government systems:**

```
apis/
├── partijhub/
│   ├── spec/
│   │   ├── partijhub-api-v1.0.0.json  ← Source of truth
│   │   ├── partijhub-api-v1.0.1.json  ← Next version (when ready)
│   │   └── CHANGELOG.md
│   └── schemas/
│       └── v1.0.0/
│           ├── request/
│           │   └── *.xsd
│           └── response/
│               └── *.xsd
```

**Commit strategy:**
```bash
# After any OpenAPI update
git add apis/partijhub/spec/partijhub-api-v1.0.0.json
python3 oic_xsd_gen.py apis/partijhub/spec/partijhub-api-v1.0.0.json -o apis/partijhub/schemas/v1.0.0
git add apis/partijhub/schemas/v1.0.0/
git commit -m "Update partijhub API v1.0.0: Added X field, fixed Y validation"
git tag -a v1.0.0 -m "Release for Q3 2024 deployment"
```

---

## Data Type Validation Reference

### String Format Specifications

| Format | Pattern Example | XSD Representation | Validation Notes |
|--------|-----------------|-------------------|------------------|
| `email` | `user@example.com` | `xs:string` | No built-in XSD validation; document format in comments |
| `uuid` | `550e8400-e29b-41d4-a716-446655440000` | `xs:string` | Standard UUID v4 format |
| `date` | `2024-03-15` | `xs:string` | ISO 8601 format (YYYY-MM-DD) |
| `date-time` | `2024-03-15T14:30:00Z` | `xs:string` | ISO 8601 with time (YYYY-MM-DDTHH:MM:SSZ) |
| `time` | `14:30:00` | `xs:string` | HH:MM:SS format |
| `uri` | `https://example.com/path` | `xs:string` | Full URI with scheme |
| `regex` | Custom pattern | `xs:string` | Document pattern in description |

### Numeric Precision

| Type | JSON Type | XSD Type | Range | Use Case |
|------|-----------|----------|-------|----------|
| Whole numbers | `integer` + `int32` | `xs:int` | -2,147,483,648 to 2,147,483,647 | Counts, quantities up to 2 billion |
| Large numbers | `integer` + `int64` | `xs:long` | -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807 | Very large IDs, timestamps |
| Money/decimals | `number` | `xs:decimal` | Arbitrary precision | Financial amounts, exact calculations |
| Floating point | `number` | `xs:double` | IEEE 754 double | Scientific calculations (NOT financial) |

---

## Implementation Checklist

### Before Going Live

- [ ] **OpenAPI Validation**
  - [ ] All operations have operationId
  - [ ] All success responses defined (200 or 201)
  - [ ] Response structure includes status + data fields
  - [ ] All properties have descriptions
  - [ ] Request bodies defined for POST/PUT/PATCH

- [ ] **XSD Validation**
  - [ ] XSD files generated successfully with no errors
  - [ ] XSD files are well-formed XML
  - [ ] No duplicate type definitions
  - [ ] Root elements match operationId naming

- [ ] **OIC Configuration**
  - [ ] REST adapter trigger created
  - [ ] Response XSD uploaded and root element selected
  - [ ] Request XSD uploaded (if applicable)
  - [ ] Mapping logic handles both SUCCESS and FAILED paths
  - [ ] Error handling populates errors array correctly

- [ ] **Testing**
  - [ ] Success path tested with valid payload
  - [ ] Error path tested with error response
  - [ ] Required fields validated (missing fields rejected)
  - [ ] Enum values validated (invalid values rejected)
  - [ ] Data type validation works (string vs number, etc.)

- [ ] **Documentation**
  - [ ] README updated with API specifics
  - [ ] CHANGELOG updated with changes
  - [ ] Troubleshooting guide updated
  - [ ] Team trained on new structure

- [ ] **Deployment**
  - [ ] Version tags created
  - [ ] Deployment plan documented
  - [ ] Rollback procedure documented
  - [ ] Stakeholders notified of changes

---

## Real-World Integration Examples

### Example 3: Government Service Integration (Complex)

**Scenario:** Belgian government service integrating MAGDA (citizen registry) with Oracle HCM

**OpenAPI Spec:**
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Person Registry API",
    "version": "1.0.0",
    "description": "Belgian Flemish Region citizen registry integration"
  },
  "paths": {
    "/v1/persons/{partyNumber}": {
      "get": {
        "operationId": "getPersonByPartyNumber",
        "description": "Retrieve complete person record including personal data, identification, and administrative status from MAGDA (Belgian citizen registry)",
        "parameters": [
          {
            "name": "partyNumber",
            "in": "path",
            "required": true,
            "description": "Oracle party number format KSZ:{11-digit-INSZ}. Example: KSZ:80010120990. INSZ is Belgian national number.",
            "schema": {
              "type": "string",
              "pattern": "^KSZ:\\d{11}$"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Person record found",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/PersonResponse" }
              }
            }
          },
          "404": {
            "description": "Person not found in MAGDA",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/PersonResponse" }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "PersonResponse": {
        "type": "object",
        "required": ["status"],
        "properties": {
          "status": {
            "type": "string",
            "enum": ["SUCCESS", "FAILED"],
            "description": "Operation outcome: SUCCESS if person found, FAILED otherwise"
          },
          "person": {
            "type": "object",
            "description": "Complete person record from MAGDA (populated on SUCCESS)",
            "properties": {
              "partyNumber": {
                "type": "string",
                "description": "Oracle party number (KSZ:INSZ format)"
              },
              "firstName": {
                "type": "string",
                "description": "First name from MAGDA → Oracle HZ_PERSON_PROFILES.PERSON_FIRST_NAME"
              },
              "lastName": {
                "type": "string",
                "description": "Last name from MAGDA → Oracle HZ_PERSON_PROFILES.PERSON_LAST_NAME"
              },
              "birthDate": {
                "type": "string",
                "format": "date",
                "description": "Date of birth in ISO 8601 format (YYYY-MM-DD)"
              },
              "identificationNumber": {
                "type": "string",
                "description": "Belgian INSZ number (11 digits)"
              },
              "nationality": {
                "type": "string",
                "description": "Country code (e.g., 'BE' for Belgium)"
              },
              "registerType": {
                "type": "string",
                "enum": ["01", "02"],
                "description": "Register type: 01 = Rijksregister (official), 02 = BIS (alternative)"
              },
              "administrativeStatus": {
                "type": "string",
                "enum": ["ACTIVE", "DECEASED", "DELETED"],
                "description": "Administrative status in MAGDA"
              }
            },
            "required": ["partyNumber", "firstName", "lastName", "identificationNumber"]
          },
          "errors": {
            "type": "array",
            "description": "Error details when status=FAILED",
            "items": {
              "type": "object",
              "properties": {
                "code": {
                  "type": "string",
                  "description": "Error code (e.g., PERSON_NOT_FOUND, INVALID_PARTY_NUMBER, MAGDA_TIMEOUT)"
                },
                "message": {
                  "type": "string",
                  "description": "Human-readable error description"
                },
                "details": {
                  "type": "object",
                  "description": "MAGDA backend details for debugging",
                  "properties": {
                    "identification": {
                      "type": "string",
                      "description": "MAGDA error ID for tracing"
                    },
                    "diagnose": {
                      "type": "string",
                      "description": "Diagnostic information from backend"
                    }
                  }
                }
              },
              "required": ["code", "message"]
            }
          }
        }
      }
    }
  }
}
```

**Generated XSD includes:**
- Full audit trail comments
- Field mappings (MAGDA → Oracle)
- Enum restrictions
- Required/optional specifications
- Deployment-ready format

---

## Validation Examples

### Valid XML Instance (Success)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GetPersonByPartyNumberResponse xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <status>SUCCESS</status>
  <person>
    <partyNumber>KSZ:80010120990</partyNumber>
    <firstName>John</firstName>
    <lastName>Doe</lastName>
    <birthDate>1980-01-12</birthDate>
    <identificationNumber>80010120990</identificationNumber>
    <nationality>BE</nationality>
    <registerType>01</registerType>
    <administrativeStatus>ACTIVE</administrativeStatus>
  </person>
</GetPersonByPartyNumberResponse>
```

**Validation against XSD:**
- ✅ status = "SUCCESS" (allowed enum value)
- ✅ person element present with all required fields
- ✅ All fields match type definitions
- ✅ No unexpected elements

### Valid XML Instance (Error)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GetPersonByPartyNumberResponse xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <status>FAILED</status>
  <errors>
    <code>PERSON_NOT_FOUND</code>
    <message>No person record found in MAGDA for KSZ:80010120990</message>
    <details>
      <identification>MAGDA_ERROR_12345</identification>
      <diagnose>Query timeout after 30 seconds attempting LDAP lookup in MAGDA</diagnose>
    </details>
  </errors>
</GetPersonByPartyNumberResponse>
```

**Validation against XSD:**
- ✅ status = "FAILED" (allowed enum value)
- ✅ person element NOT present (correct for error)
- ✅ errors array present with details
- ✅ All error fields properly formatted

### Invalid XML Instance (Will Fail)

```xml
<!-- INVALID: status has wrong value -->
<GetPersonByPartyNumberResponse>
  <status>ERROR</status>  <!-- ❌ Not in enum [SUCCESS, FAILED] -->
  <person>...</person>
</GetPersonByPartyNumberResponse>

<!-- INVALID: missing required field -->
<GetPersonByPartyNumberResponse>
  <status>SUCCESS</status>
  <person>
    <partyNumber>KSZ:80010120990</partyNumber>
    <firstName>John</firstName>
    <!-- ❌ lastName is required but missing -->
  </person>
</GetPersonByPartyNumberResponse>

<!-- INVALID: wrong data type -->
<GetPersonByPartyNumberResponse>
  <status>SUCCESS</status>
  <person>
    <partyNumber>KSZ:80010120990</partyNumber>
    <firstName>John</firstName>
    <lastName>Doe</lastName>
    <birthDate>January 12, 1980</birthDate>  <!-- ❌ Not ISO 8601 format -->
  </person>
</GetPersonByPartyNumberResponse>
```

---

## Performance & Scalability

### Generation Performance

- **Small API (< 10 operations):** ~100ms
- **Medium API (10-50 operations):** ~200-500ms
- **Large API (50+ operations):** ~1-2 seconds

*Times include: OpenAPI parsing, reference resolution, XSD generation, file I/O*

### XSD Validation in OIC Runtime

OIC Gen3 validates incoming requests and responses against XSD:
- **Per-request overhead:** ~10-50ms (depending on payload complexity)
- **Type checking:** Automatic (no custom code needed)
- **Enum validation:** Automatic (invalid values rejected)
- **Required field validation:** Automatic (missing fields cause error)

### Optimization Tips

1. **Keep schemas focused:** One operation per XSD, not one mega-schema
2. **Use enums:** Reduces validation overhead vs. free-text strings
3. **Minimize nesting:** Deep hierarchies slow validation slightly
4. **Use appropriate types:** `xs:int` faster than `xs:string` with pattern

---

## Support & Contact

For issues, questions, or contributions:

1. **Check the Troubleshooting section** above (covers 90% of issues)
2. **Validate your OpenAPI spec** against the OpenAPI requirements section
3. **Review the examples** to ensure your structure matches the pattern
4. **Check generated XSD files** for validity with XML tools
5. **Review the Implementation Checklist** before deploying

---

## FAQ - Frequently Asked Questions

### Q: Why do I need `minOccurs` and `maxOccurs` in XSD?

**A:** These tell OIC Gen3 what fields are required and what can repeat:
- `minOccurs="1"` = field MUST be present
- `minOccurs="0"` = field is optional
- `maxOccurs="1"` = field appears once
- `maxOccurs="unbounded"` = field is an array (can repeat)

### Q: Can I use different status values like "OK" or "ERROR"?

**A:** No, stick to `"SUCCESS"` and `"FAILED"`. These are OIC Gen3 conventions. Using different values requires custom mapping logic in OIC.

### Q: What happens if my OpenAPI spec changes?

**A:** Regenerate the XSD and redeploy to OIC. Version control tracks both spec and XSD changes together.

### Q: Is the tool free to use?

**A:** Yes, it's Apache License 2.0. You can use, modify, and distribute freely.

### Q: Can I use this with other integration platforms?

**A:** The tool generates standard XSD. Any platform accepting XSD can use it (OIC, Mulesoft, etc.).

### Q: What if my response doesn't have a status field?

**A:** That won't work with OIC Gen3. All responses must have status="SUCCESS" or "FAILED" for the polymorphic pattern to work.

---

## References

- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.3)
- [XML Schema (XSD) Reference](https://www.w3.org/TR/xmlschema-1/)
- [Oracle Integration Cloud Documentation](https://docs.oracle.com/en/cloud/paas/integration-cloud/)
- [JSON Schema Reference](https://json-schema.org/)
- [W3C XML Validation](https://www.w3.org/XML/Schema)

---

## License

Apache License 2.0 — See LICENSE file for details.
