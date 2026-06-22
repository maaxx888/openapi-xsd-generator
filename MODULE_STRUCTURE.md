# Module Structure

The codebase has been refactored from a single monolithic script (`oic_xsd_gen.py`) into a well-organized package (`oic_generator/`) with the following modules:

## Core Modules

### 1. **constants.py** - Global Constants
- `XS_NS`: XML Schema namespace
- `HTTP_METHODS`: Set of valid HTTP methods
- `FACET_KEYS`: Tuple of JSON Schema constraint keys

### 2. **loader.py** - Document Loading & Reference Resolution
- `load_document(path)`: Load OpenAPI JSON/YAML files
- `resolve_refs(document, source_path)`: Resolve JSON references in OpenAPI spec

### 3. **utils.py** - Utility Functions
- `pascal_case()`: Convert strings to PascalCase
- `kebab_case()`: Convert strings to kebab-case  
- `singular_name()`: Convert plural names to singular
- `xs_tag()`: Create XML Schema namespace tags

### 4. **io.py** - File I/O Operations
- `write_json_file()`: Write JSON files with formatting
- `write_text_file()`: Write text/XSD files
- `get_output_base_dir()`: Determine output directory

## Schema & Type Analysis

### 5. **schema.py** - Schema Manipulation & Analysis
- `schema_type()`: Extract type from JSON schema
- `is_nullable()`: Check if schema is nullable
- `is_object_schema()`: Check if schema represents an object
- `is_array_schema()`: Check if schema represents an array
- `resolve_schema()`: Resolve allOf/oneOf/anyOf combinators
- `deep_merge_schemas()`: Merge JSON schemas with conflict resolution
- `build_description()`: Build XSD documentation from schema

### 6. **types.py** - JSON → XSD Type Mapping
- `infer_xs_type()`: Map JSON Schema types to XSD types
- `xs_base_supports_string_facets()`: Check string constraint support
- `xs_base_supports_numeric_facets()`: Check numeric constraint support

### 7. **facets.py** - XSD Constraints (Facets)
- `apply_numeric_facets()`: Apply numeric constraints (min/max/etc)
- `apply_string_facets()`: Apply string constraints (length/pattern)
- `apply_schema_facets()`: Apply all applicable constraints

## XSD Generation

### 8. **xml_builder.py** - Low-level XSD Element Construction
- `indent_xml()`: Format XSD with proper indentation
- `add_comment_before_element()`: Add comments to XSD
- `add_section_header()`: Add section headers to XSD
- `add_restricted_simple_type()`: Create XSD simpleType with restrictions
- `add_property_element()`: Add element to XSD complexType
- `add_complex_type()`: Create XSD complexType
- `add_status_type()`: Create standard StatusType
- `add_error_types_from_schema()`: Generate error response types
- `add_fallback_error_types()`: Add default error types

### 9. **xsd.py** - High-level XSD Schema Generation
- `generate_oic_request_xsd()`: Generate XSD for request payloads
- `generate_oic_xsd()`: Generate XSD for response payloads
- `add_data_property_to_xsd()`: Add data properties to response XSD

## OpenAPI Processing

### 10. **operations.py** - OpenAPI Operation Analysis
- `find_json_response_schema()`: Extract JSON response schema
- `find_json_request_schema()`: Extract JSON request schema
- `extract_error_schemas()`: Find error response schemas
- `merge_error_response_schemas()`: Combine error schemas
- `merge_response_schemas_with_errors()`: Merge success & error schemas
- `find_success_response()`: Find 2xx/201 response
- `detect_data_properties()`: Identify data payload fields
- `detect_envelope_fields()`: Identify wrapper/envelope fields
- `operation_root_name()`: Generate root element name

### 11. **discovery.py** - OpenAPI Operations Discovery
- `discover_operations()`: Extract all operations from OpenAPI spec
- `display_operations_by_tag()`: Format operations for user display
- `method_upper()`: Uppercase HTTP method

### 12. **processor.py** - Main Processing Pipeline
- `process_openapi()`: Main entry point that orchestrates:
  - Loading OpenAPI document
  - Finding operations
  - Generating XSD/JSON schemas
  - Writing output files

## User Interface & CLI

### 13. **ui.py** - Interactive User Input
- `get_user_selection()`: Prompt user to select operations

### 14. **output.py** - Result Formatting
- `print_results()`: Display generated files summary

### 15. **cli.py** - Command-line Interface
- `main()`: CLI entry point with argument parsing
  - `-o/--output`: Custom output directory
  - `-a/--all`: Convert all operations
  - `-s/--select`: Select specific operations

## Entry Point

### **oic_xsd_gen.py**
Lightweight entry point that imports and calls `cli.main()`

## Key Design Patterns

1. **Separation of Concerns**: Each module handles specific responsibilities
2. **Layered Architecture**:
   - Low-level: constants, utils, io
   - Mid-level: schema, types, facets  
   - High-level: xml_builder, xsd, operations
   - Top-level: processor, discovery, cli
3. **Composability**: Functions are small and composable
4. **Type Hints**: All functions use type annotations
5. **No Comments**: Code is self-documenting through clear naming

## Backward Compatibility

- Original `oic_xsd_gen.py` preserved as entry point
- Test imports updated to use new module structure
- All existing tests pass without modification
