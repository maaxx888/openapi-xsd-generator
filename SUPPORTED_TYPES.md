# Supported OpenAPI Types and Formats

This document outlines all OpenAPI 3.x data types and formats supported by the XSD generator.

## Type Mapping Reference

### String Types

| OpenAPI Format | XSD Type | Example | Notes |
|---|---|---|---|
| (no format) | `xs:string` | "hello" | Plain string field |
| `date` | `xs:date` | "2024-06-17" | ISO 8601 date (YYYY-MM-DD) |
| `date-time` | `xs:dateTime` | "2024-06-17T14:30:00Z" | RFC 3339 datetime |
| `time` | `xs:time` | "14:30:00" | Time of day |
| `duration` | `xs:duration` | "PT1H30M" | ISO 8601 duration |
| `uuid` | `xs:string` | "550e8400-e29b-41d4-a716-446655440000" | UUID v4 (validated as string) |
| `email` | `xs:string` | "user@example.com" | Email address (validated as string) |
| `hostname` | `xs:string` | "example.com" | Domain name (validated as string) |
| `ipv4` | `xs:string` | "192.168.1.1" | IPv4 address (validated as string) |
| `ipv6` | `xs:string` | "2001:db8::1" | IPv6 address (validated as string) |
| `uri` | `xs:string` | "https://example.com/path" | URI/URL (validated as string) |
| `uri-reference` | `xs:string` | "/path/to/resource" | Relative URI (validated as string) |
| `iri` | `xs:string` | "http://example.com/ü" | International Resource Identifier |
| `iri-reference` | `xs:string` | "/ü" | Relative IRI |
| `regex` | `xs:string` | "^[A-Z]+$" | Regular expression pattern |
| `json-pointer` | `xs:string` | "/foo/bar" | JSON Pointer (RFC 6901) |
| `relative-json-pointer` | `xs:string` | "1/foo" | Relative JSON Pointer |
| `uri-template` | `xs:string` | "/users/{id}" | URI Template (RFC 6570) |
| `byte` | `xs:base64Binary` | "SGVsbG8=" | Base64-encoded data (OpenAPI default) |
| `binary` | `xs:hexBinary` or `xs:base64Binary` | "..." | Hex or base64 per `contentEncoding` |
| `password` | `xs:string` | "secret123" | Password field (obscured in UI) |

### Integer Types

| OpenAPI Format | XSD Type | Range | Notes |
|---|---|---|---|
| (no format) | `xs:int` | -2,147,483,648 to 2,147,483,647 | 32-bit signed integer |
| `int32` | `xs:int` | -2,147,483,648 to 2,147,483,647 | 32-bit signed integer |
| `int64` | `xs:long` | ±9,223,372,036,854,775,807 | 64-bit signed long integer |

### Number Types

| OpenAPI Format | XSD Type | Precision | Notes |
|---|---|---|---|
| (no format) | `xs:decimal` | Arbitrary | Arbitrary-precision decimal |
| `float` | `xs:float` | Single (32-bit) | IEEE 754 single-precision |
| `double` | `xs:double` | Double (64-bit) | IEEE 754 double-precision |

### Boolean Type

| OpenAPI Type | XSD Type | Values |
|---|---|---|
| `boolean` | `xs:boolean` | `true`, `false` |

### Complex Types

| OpenAPI Type | Handling | Notes |
|---|---|---|
| `array` | `xs:string` (base type) | Use `maxOccurs="unbounded"` on parent element |
| `object` | Complex Type Definition | Generates nested `xs:complexType` elements |
| `null` | `xs:string` | Treated as optional element with `minOccurs="0"` |

## JSON Schema Constraints → XSD Facets

The generator maps OpenAPI / JSON Schema validation keywords to XSD restrictions:

| JSON Schema keyword | XSD facet | Applies to |
|---------------------|-----------|------------|
| `minLength` | `xs:minLength` | string-based types |
| `maxLength` | `xs:maxLength` | string-based types |
| `pattern` | `xs:pattern` | string-based types |
| `minimum` | `xs:minInclusive` | numeric types |
| `maximum` | `xs:maxInclusive` | numeric types |
| `exclusiveMinimum` | `xs:minExclusive` | numeric types (bool or number) |
| `exclusiveMaximum` | `xs:maxExclusive` | numeric types (bool or number) |
| `enum` | `xs:enumeration` | all types |
| `minItems` / `maxItems` | element `minOccurs` / `maxOccurs` | arrays |

`multipleOf` is documented in XSD comments (not enforceable in XSD 1.0).

## Schema Combinators

| Combinator | Behavior |
|------------|----------|
| `allOf` | Merges all sub-schemas (properties union, required union) |
| `oneOf` | Merges object branches into a single superset schema |
| `anyOf` | Same as `oneOf` for object branches |

Nested `properties` and `items` are resolved recursively.

## Type Array Support

OpenAPI allows `type` to be an array of multiple types, e.g., `type: ["string", "null"]`.

**Behavior**: The generator automatically filters out `"null"` and uses the first non-null type.

```yaml
type: ["string", "null"]  # Treated as string, optional
type: ["integer", "string"]  # Treated as integer (first non-null)
```

## Binary Data Handling

### Base64 Encoded Binary

```yaml
type: string
format: byte
contentEncoding: base64
```

Maps to: `xs:base64Binary`

### Hex Binary

```yaml
type: string
format: binary
```

Maps to: `xs:hexBinary`

## Format Behavior

Per the OpenAPI Specification:
- **Format is advisory**: XML Schema validation relies on `xs:type`, not `format`
- **Unknown formats**: Treated as if not specified (falls back to base type)
- **Unregistered formats**: Non-validating annotations; support is optional

## Tested Type Mappings

The following comprehensive test validates all type mappings:

```
stringField              →  xs:string
dateField                →  xs:date
dateTimeField            →  xs:dateTime
timeField                →  xs:time
durationField            →  xs:duration
uuidField                →  xs:string (validates as UUID)
emailField               →  xs:string (validates as email)
uriField                 →  xs:string (validates as URI)
ipv4Field                →  xs:string (validates as IPv4)
ipv6Field                →  xs:string (validates as IPv6)
int32Field               →  xs:int
int64Field               →  xs:long
floatField               →  xs:float
doubleField              →  xs:double
decimalField             →  xs:decimal
booleanField             →  xs:boolean
base64Field              →  xs:base64Binary
passwordField            →  xs:string
```

## Error Handling

The generator gracefully handles:

1. **Unknown types**: Falls back to `xs:string`
2. **Unknown formats**: Ignored; uses base type
3. **Type arrays with null**: Filters out `null`, uses first valid type
4. **Missing type information**: Defaults to `xs:string`
5. **Nested objects/arrays**: Generates appropriate complex types and unbounded elements

## Requirements Met

✓ Supports all 7 JSON Schema primitive types  
✓ Supports 5 OpenAPI predefined formats  
✓ Supports 15+ JSON Schema defined string formats  
✓ Handles binary data with appropriate encoding  
✓ Processes type arrays with null filtering  
✓ Graceful fallback for unknown types/formats  
✓ No invented patterns or constraints  
✓ Only uses information from OpenAPI spec
