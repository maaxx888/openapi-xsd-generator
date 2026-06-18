#!/usr/bin/env python3

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace, Comment
import yaml
import jsonref


XS_NS = "http://www.w3.org/2001/XMLSchema"
register_namespace("xs", XS_NS)

HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
}

FACET_KEYS = (
    "pattern",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
)


def load_document(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        if path.suffix.lower() in [".yaml", ".yml"]:
            return yaml.safe_load(file)
        return json.load(file)


def resolve_refs(document: dict, source_path: Path) -> dict:
    base_uri = source_path.resolve().as_uri()
    resolved = jsonref.replace_refs(
        document,
        base_uri=base_uri,
        lazy_load=False,
        load_on_repr=True,
    )

    def convert_to_dict(obj):
        if isinstance(obj, dict):
            return {k: convert_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_dict(item) for item in obj]
        else:
            return obj

    return convert_to_dict(resolved)


def pascal_case(value: str) -> str:
    value = value.replace("_", "-")
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value)
    parts = re.split(r"[^A-Za-z0-9]+", value)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def kebab_case(value: str) -> str:
    value = value.replace("_", "-")
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value)
    value = re.sub(r"[^A-Za-z0-9]+", "-", value)
    return value.strip("-").lower()


def singular_name(value: str) -> str:
    if value.endswith("ies"):
        return value[:-3] + "y"

    if value.endswith("ses"):
        return value[:-2]

    if value.endswith("s") and not value.endswith("ss"):
        return value[:-1]

    return value


def xs_tag(local_name: str) -> str:
    return f"{{{XS_NS}}}{local_name}"


def indent_xml(element, level=0):
    whitespace = "\n" + level * "  "

    if len(element):
        if not element.text or not element.text.strip():
            element.text = whitespace + "  "

        for child in element:
            indent_xml(child, level + 1)

        if not child.tail or not child.tail.strip():
            child.tail = whitespace

    if level and (not element.tail or not element.tail.strip()):
        element.tail = whitespace


def add_comment_before_element(parent: Element, text: str):
    if text and text.strip():
        comment = Comment(" " + text.strip() + " ")
        parent.append(comment)


def add_section_header(parent: Element, title: str):
    if title and title.strip():
        separator = "=" * 60
        comment_text = f"\n{separator}\n{title.strip()}\n{separator}\n"
        comment = Comment(comment_text)
        parent.append(comment)


def schema_type(schema: dict):
    value = schema.get("type")

    if isinstance(value, list):
        non_null_values = [item for item in value if item != "null"]
        if non_null_values:
            return non_null_values[0]
        return "string"

    return value


def is_nullable(schema: dict) -> bool:
    if schema.get("nullable"):
        return True

    schema_type_value = schema.get("type")
    if isinstance(schema_type_value, list) and "null" in schema_type_value:
        return True

    return False


def is_object_schema(schema: dict) -> bool:
    if not isinstance(schema, dict):
        return False

    return schema_type(schema) == "object" or "properties" in schema


def is_array_schema(schema: dict) -> bool:
    if not isinstance(schema, dict):
        return False

    return schema_type(schema) == "array"


def has_constraint_facets(schema: dict) -> bool:
    return any(key in schema for key in FACET_KEYS)


def needs_named_simple_type(schema: dict) -> bool:
    return "enum" in schema or has_constraint_facets(schema)


def build_description(schema: dict) -> str:
    parts = []

    if schema.get("description"):
        parts.append(str(schema["description"]).strip())

    if "default" in schema:
        parts.append(f"Default: {schema['default']}")

    if "example" in schema:
        parts.append(f"Example: {schema['example']}")

    if schema.get("readOnly"):
        parts.append("Read-only")

    if schema.get("writeOnly"):
        parts.append("Write-only")

    if schema.get("deprecated"):
        parts.append("Deprecated")

    if is_nullable(schema):
        parts.append("Nullable")

    if schema.get("additionalProperties") is False:
        parts.append("additionalProperties: false")

    return " | ".join(parts)


def deep_merge_schemas(
    base: dict,
    overlay: dict,
    required_mode: str = "intersection",
) -> dict:
    if not base:
        return copy.deepcopy(overlay)

    if not overlay:
        return copy.deepcopy(base)

    result = copy.deepcopy(base)

    for key, value in overlay.items():
        if key == "properties":
            overlay_properties = value or {}
            result_properties = result.setdefault("properties", {})

            for property_name, property_schema in overlay_properties.items():
                if property_name in result_properties:
                    result_properties[property_name] = deep_merge_schemas(
                        result_properties[property_name],
                        property_schema,
                        required_mode=required_mode,
                    )
                else:
                    result_properties[property_name] = copy.deepcopy(property_schema)
        elif key == "required":
            overlay_required = set(value or [])
            base_required = set(result.get("required", []) or [])

            if required_mode == "union":
                result["required"] = sorted(base_required | overlay_required)
            else:
                result["required"] = sorted(base_required & overlay_required)
        elif key == "enum":
            combined = list(
                dict.fromkeys((result.get("enum", []) or []) + (value or []))
            )
            result["enum"] = combined
        elif key in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
            if key not in result:
                result[key] = value
        elif key in ("minLength", "maxLength", "pattern", "multipleOf"):
            if key not in result:
                result[key] = value
        elif key in ("minItems", "maxItems"):
            if key not in result:
                result[key] = value
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge_schemas(
                result[key],
                value,
                required_mode=required_mode,
            )
        elif key not in result:
            result[key] = copy.deepcopy(value)

    return result


def merge_schema_branches(branches: list[dict]) -> dict:
    merged = {}

    for branch in branches:
        if isinstance(branch, dict):
            merged = deep_merge_schemas(merged, branch, required_mode="union")

    return merged


def resolve_schema(schema: dict) -> dict:
    if not isinstance(schema, dict):
        return schema

    combinator_keys = ("allOf", "oneOf", "anyOf")
    combinator_present = any(key in schema for key in combinator_keys)

    if combinator_present:
        merged = {}

        if "allOf" in schema:
            for sub_schema in schema["allOf"]:
                merged = deep_merge_schemas(
                    merged,
                    resolve_schema(sub_schema),
                    required_mode="union",
                )

        if "oneOf" in schema:
            branches = [resolve_schema(sub_schema) for sub_schema in schema["oneOf"]]
            merged = deep_merge_schemas(
                merged,
                merge_schema_branches(branches),
                required_mode="union",
            )

        if "anyOf" in schema:
            branches = [resolve_schema(sub_schema) for sub_schema in schema["anyOf"]]
            merged = deep_merge_schemas(
                merged,
                merge_schema_branches(branches),
                required_mode="union",
            )

        remaining = {
            key: value
            for key, value in schema.items()
            if key not in combinator_keys
        }

        if remaining:
            merged = deep_merge_schemas(merged, resolve_schema(remaining))

        schema = merged

    result = copy.deepcopy(schema)

    if "properties" in result:
        result["properties"] = {
            property_name: resolve_schema(property_schema)
            for property_name, property_schema in (result.get("properties") or {}).items()
        }

    if "items" in result and isinstance(result["items"], dict):
        result["items"] = resolve_schema(result["items"])

    return result


def infer_xs_type(schema: dict) -> str:
    current_type = schema_type(schema)
    current_format = schema.get("format")
    content_media_type = schema.get("contentMediaType")
    content_encoding = schema.get("contentEncoding")

    if current_type == "string":
        if current_format:
            if current_format == "date":
                return "xs:date"
            elif current_format in ("date-time", "datetime"):
                return "xs:dateTime"
            elif current_format == "time":
                return "xs:time"
            elif current_format == "duration":
                return "xs:duration"
            elif current_format in (
                "uuid",
                "email",
                "hostname",
                "ipv4",
                "ipv6",
                "uri",
                "uri-reference",
                "iri",
                "iri-reference",
                "regex",
                "json-pointer",
                "relative-json-pointer",
                "uri-template",
                "password",
            ):
                return "xs:string"
            elif current_format == "byte":
                if content_encoding in ("base64", "base64url"):
                    return "xs:base64Binary"
                return "xs:base64Binary"
            elif current_format == "binary":
                if content_encoding in ("base64", "base64url"):
                    return "xs:base64Binary"
                return "xs:hexBinary"

        if content_media_type:
            if content_encoding in ("base64", "base64url"):
                return "xs:base64Binary"
            return "xs:hexBinary"

        return "xs:string"

    if current_type == "integer":
        if current_format == "int64":
            return "xs:long"
        return "xs:int"

    if current_type == "number":
        if current_format == "float":
            return "xs:float"
        elif current_format == "double":
            return "xs:double"
        return "xs:decimal"

    if current_type == "boolean":
        return "xs:boolean"

    return "xs:string"


def xs_base_supports_string_facets(base_type: str) -> bool:
    local_name = base_type.replace("xs:", "")
    return local_name in (
        "string",
        "date",
        "dateTime",
        "time",
        "duration",
        "token",
        "normalizedString",
    )


def xs_base_supports_numeric_facets(base_type: str) -> bool:
    local_name = base_type.replace("xs:", "")
    return local_name in ("int", "long", "decimal", "float", "double", "byte", "short")


def apply_numeric_facets(restriction: Element, schema: dict):
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    exclusive_minimum = schema.get("exclusiveMinimum")
    exclusive_maximum = schema.get("exclusiveMaximum")

    if exclusive_minimum is True and minimum is not None:
        SubElement(restriction, xs_tag("minExclusive"), {"value": str(minimum)})
    elif isinstance(exclusive_minimum, (int, float)):
        SubElement(restriction, xs_tag("minExclusive"), {"value": str(exclusive_minimum)})
    elif minimum is not None:
        SubElement(restriction, xs_tag("minInclusive"), {"value": str(minimum)})

    if exclusive_maximum is True and maximum is not None:
        SubElement(restriction, xs_tag("maxExclusive"), {"value": str(maximum)})
    elif isinstance(exclusive_maximum, (int, float)):
        SubElement(restriction, xs_tag("maxExclusive"), {"value": str(exclusive_maximum)})
    elif maximum is not None:
        SubElement(restriction, xs_tag("maxInclusive"), {"value": str(maximum)})

    if "multipleOf" in schema:
        add_comment_before_element(
            restriction,
            f"multipleOf: {schema['multipleOf']} (not enforced in XSD 1.0)",
        )


def apply_string_facets(restriction: Element, schema: dict, base_type: str):
    if not xs_base_supports_string_facets(base_type):
        return

    if "minLength" in schema:
        SubElement(
            restriction,
            xs_tag("minLength"),
            {"value": str(schema["minLength"])},
        )

    if "maxLength" in schema:
        SubElement(
            restriction,
            xs_tag("maxLength"),
            {"value": str(schema["maxLength"])},
        )

    if "pattern" in schema:
        SubElement(
            restriction,
            xs_tag("pattern"),
            {"value": schema["pattern"]},
        )


def apply_schema_facets(restriction: Element, schema: dict, base_type: str):
    apply_string_facets(restriction, schema, base_type)

    if xs_base_supports_numeric_facets(base_type):
        apply_numeric_facets(restriction, schema)


def add_restricted_simple_type(
    schema_element: Element,
    type_name: str,
    schema: dict,
    generated_types: set[str],
):
    if type_name in generated_types:
        return

    generated_types.add(type_name)
    schema = resolve_schema(schema)
    base_type = infer_xs_type(schema)

    add_section_header(schema_element, type_name)
    simple_type = SubElement(
        schema_element,
        xs_tag("simpleType"),
        {"name": type_name},
    )

    restriction = SubElement(
        simple_type,
        xs_tag("restriction"),
        {"base": base_type},
    )

    if "enum" in schema:
        for value in schema["enum"]:
            SubElement(
                restriction,
                xs_tag("enumeration"),
                {"value": str(value)},
            )

    apply_schema_facets(restriction, schema, base_type)


def get_or_create_element_type(
    schema_element: Element,
    type_name: str,
    schema: dict,
    generated_types: set[str],
) -> str:
    schema = resolve_schema(schema)

    if needs_named_simple_type(schema):
        add_restricted_simple_type(schema_element, type_name, schema, generated_types)
        return type_name

    return infer_xs_type(schema)


def property_min_occurs(property_name: str, property_schema: dict, required: set[str]) -> str:
    if is_nullable(property_schema):
        return "0"

    return "1" if property_name in required else "0"


def array_occurs(
    property_name: str,
    property_schema: dict,
    required: set[str],
) -> tuple[str, str]:
    min_items = property_schema.get("minItems")
    max_items = property_schema.get("maxItems")

    if min_items is not None:
        min_occurs = str(min_items)
    else:
        min_occurs = property_min_occurs(property_name, property_schema, required)

    max_occurs = str(max_items) if max_items is not None else "unbounded"
    return min_occurs, max_occurs


def nested_type_name(parent_type_name: str, property_name: str, suffix: str = "Type") -> str:
    parent_base = parent_type_name
    if parent_base.endswith("Type"):
        parent_base = parent_base[:-4]

    return parent_base + pascal_case(property_name) + suffix


def add_property_element(
    sequence: Element,
    schema_element: Element,
    property_name: str,
    property_schema: dict,
    required: set[str],
    generated_types: set[str],
    parent_type_name: str,
    skip_names: set[str] | None = None,
):
    if skip_names and property_name in skip_names:
        return

    property_schema = resolve_schema(property_schema)
    description = build_description(property_schema)

    if is_array_schema(property_schema):
        item_schema = property_schema.get("items", {}) or {}
        item_schema = resolve_schema(item_schema)
        min_occurs, max_occurs = array_occurs(property_name, property_schema, required)

        if is_object_schema(item_schema):
            item_type_name = nested_type_name(
                parent_type_name,
                singular_name(property_name),
                "ItemType",
            )
            add_complex_type(
                schema_element,
                item_type_name,
                item_schema,
                generated_types,
            )
            element_type = item_type_name
        else:
            item_type_name = nested_type_name(
                parent_type_name,
                singular_name(property_name),
                "ItemType",
            )
            element_type = get_or_create_element_type(
                schema_element,
                item_type_name,
                item_schema,
                generated_types,
            )

        add_comment_before_element(sequence, description)
        SubElement(
            sequence,
            xs_tag("element"),
            {
                "name": property_name,
                "type": element_type,
                "minOccurs": min_occurs,
                "maxOccurs": max_occurs,
            },
        )
        return

    if is_object_schema(property_schema):
        child_type_name = nested_type_name(parent_type_name, property_name)
        add_complex_type(
            schema_element,
            child_type_name,
            property_schema,
            generated_types,
        )

        add_comment_before_element(sequence, description)
        SubElement(
            sequence,
            xs_tag("element"),
            {
                "name": property_name,
                "type": child_type_name,
                "minOccurs": property_min_occurs(property_name, property_schema, required),
                "maxOccurs": "1",
            },
        )
        return

    type_name = nested_type_name(parent_type_name, property_name)
    element_type = get_or_create_element_type(
        schema_element,
        type_name,
        property_schema,
        generated_types,
    )

    add_comment_before_element(sequence, description)
    SubElement(
        sequence,
        xs_tag("element"),
        {
            "name": property_name,
            "type": element_type,
            "minOccurs": property_min_occurs(property_name, property_schema, required),
            "maxOccurs": "1",
        },
    )


def add_complex_type(
    schema_element: Element,
    type_name: str,
    json_schema: dict,
    generated_types: set[str],
    skip_names: set[str] | None = None,
):
    if type_name in generated_types:
        return

    generated_types.add(type_name)
    json_schema = resolve_schema(json_schema)

    add_section_header(schema_element, type_name)

    type_description = build_description(json_schema)
    if type_description:
        add_comment_before_element(schema_element, type_description)

    complex_type = SubElement(
        schema_element,
        xs_tag("complexType"),
        {"name": type_name},
    )

    sequence = SubElement(complex_type, xs_tag("sequence"))
    properties = json_schema.get("properties", {}) or {}
    required = set(json_schema.get("required", []) or [])

    for property_name, property_schema in properties.items():
        add_property_element(
            sequence,
            schema_element,
            property_name,
            property_schema,
            required,
            generated_types,
            type_name,
            skip_names=skip_names,
        )


def add_status_type(schema_element: Element, response_schema: dict | None = None):
    status_values = ["SUCCESS", "FAILED"]

    if response_schema:
        status_schema = (response_schema.get("properties", {}) or {}).get("status")
        if status_schema:
            status_schema = resolve_schema(status_schema)
            if "enum" in status_schema:
                status_values = list(dict.fromkeys(status_schema["enum"]))

    add_section_header(schema_element, "StatusType")
    simple_type = SubElement(
        schema_element,
        xs_tag("simpleType"),
        {"name": "StatusType"},
    )

    restriction = SubElement(
        simple_type,
        xs_tag("restriction"),
        {"base": "xs:string"},
    )

    for value in status_values:
        SubElement(
            restriction,
            xs_tag("enumeration"),
            {"value": str(value)},
        )


def add_error_types_from_schema(
    schema_element: Element,
    response_schema: dict,
    generated_types: set[str],
):
    errors_schema = (response_schema.get("properties", {}) or {}).get("errors")

    if not errors_schema:
        add_fallback_error_types(schema_element, generated_types)
        return

    errors_schema = resolve_schema(errors_schema)
    item_schema = errors_schema.get("items", {}) or {}
    item_schema = resolve_schema(item_schema)

    if is_object_schema(item_schema):
        add_complex_type(
            schema_element,
            "ErrorItemType",
            item_schema,
            generated_types,
        )
        return

    add_fallback_error_types(schema_element, generated_types)


def add_fallback_error_types(schema_element: Element, generated_types: set[str]):
    details_type_schema = {
        "type": "object",
        "properties": {
            "identification": {"type": "string", "description": "Error identification code"},
            "diagnose": {"type": "string", "description": "Error diagnostic message"},
        },
    }

    add_complex_type(
        schema_element,
        "ErrorDetailsType",
        details_type_schema,
        generated_types,
    )

    error_item_schema = {
        "type": "object",
        "required": ["code", "message"],
        "properties": {
            "code": {"type": "string", "description": "Machine-readable error code"},
            "message": {"type": "string", "description": "Human-readable error message"},
            "details": {
                "type": "object",
                "description": "Error details (backend-specific)",
                "properties": details_type_schema["properties"],
            },
        },
    }

    add_complex_type(
        schema_element,
        "ErrorItemType",
        error_item_schema,
        generated_types,
    )


def find_json_response_schema(response: dict) -> dict | None:
    content = response.get("content", {}) or {}

    if "application/json" in content:
        return content["application/json"].get("schema")

    for content_type, content_definition in content.items():
        if content_type.endswith("+json"):
            return content_definition.get("schema")

    return None


def find_json_request_schema(request_body: dict) -> dict | None:
    if not request_body:
        return None

    content = request_body.get("content", {}) or {}

    if "application/json" in content:
        return content["application/json"].get("schema")

    for content_type, content_definition in content.items():
        if content_type.endswith("+json"):
            return content_definition.get("schema")

    return None


def extract_error_schemas(operation: dict) -> list[dict]:
    responses = operation.get("responses", {}) or {}
    error_schemas = []

    for status_code, response in responses.items():
        status_int = int(status_code) if status_code.isdigit() else None
        if status_int and status_int >= 400:
            error_schema = find_json_response_schema(response)
            if error_schema:
                error_schemas.append(resolve_schema(error_schema))

    return error_schemas


def merge_error_response_schemas(error_schemas: list[dict]) -> dict | None:
    if not error_schemas:
        return None

    merged = error_schemas[0]

    for error_schema in error_schemas[1:]:
        merged = deep_merge_schemas(
            merged,
            error_schema,
            required_mode="intersection",
        )

    return merged


def merge_response_schemas_with_errors(operation: dict) -> dict | None:
    responses = operation.get("responses", {}) or {}

    success_schema = None
    error_schemas = []

    for status_code, response in responses.items():
        status_int = int(status_code) if status_code.isdigit() else None

        if status_int in (200, 201):
            success_schema = find_json_response_schema(response)
        elif status_int and status_int >= 400:
            error_schema = find_json_response_schema(response)
            if error_schema:
                error_schemas.append(error_schema)

    if not success_schema:
        return None

    success_schema = resolve_schema(success_schema)

    if not error_schemas:
        return success_schema

    merged_schema = success_schema

    for error_schema in error_schemas:
        merged_schema = deep_merge_schemas(
            merged_schema,
            resolve_schema(error_schema),
            required_mode="intersection",
        )

    return merged_schema


def find_success_response(operation: dict) -> tuple[str, dict] | tuple[None, None]:
    responses = operation.get("responses", {}) or {}

    for status_code in ["200", "201"]:
        if status_code in responses:
            return status_code, responses[status_code]

    return None, None


def detect_data_properties(response_schema: dict) -> list[tuple[str, dict]]:
    properties = response_schema.get("properties", {}) or {}
    ignored_properties = {"status", "errors"}

    return [
        (property_name, property_schema)
        for property_name, property_schema in properties.items()
        if property_name not in ignored_properties
    ]


def operation_root_name(operation_id: str) -> str:
    name = pascal_case(operation_id)

    if name.endswith("Response"):
        return name

    return name + "Response"


def generate_oic_request_xsd(operation_id: str, request_schema: dict) -> str:
    root_name = pascal_case(operation_id) + "Request"
    root_type_name = root_name + "Type"
    request_schema = resolve_schema(request_schema)

    schema_element = Element(
        xs_tag("schema"),
        {
            "elementFormDefault": "unqualified",
        },
    )

    SubElement(
        schema_element,
        xs_tag("element"),
        {
            "name": root_name,
            "type": root_type_name,
        },
    )

    generated_types = set()

    if is_array_schema(request_schema):
        item_schema = request_schema.get("items", {}) or {}
        add_complex_type(
            schema_element,
            root_type_name,
            item_schema,
            generated_types,
        )
    elif is_object_schema(request_schema):
        add_complex_type(
            schema_element,
            root_type_name,
            request_schema,
            generated_types,
        )
    else:
        add_restricted_simple_type(
            schema_element,
            root_type_name,
            request_schema,
            generated_types,
        )

    indent_xml(schema_element)

    return tostring(
        schema_element,
        encoding="utf-8",
        xml_declaration=True,
    ).decode("utf-8")


def add_data_property_to_xsd(
    schema_element: Element,
    root_sequence: Element,
    data_property_name: str,
    data_property_schema: dict,
    generated_types: set[str],
):
    data_property_schema = resolve_schema(data_property_schema)
    data_type_name = pascal_case(data_property_name) + "ResponseType"

    add_comment_before_element(
        root_sequence,
        f"Filled on SUCCESS (from {data_property_name})",
    )
    SubElement(
        root_sequence,
        xs_tag("element"),
        {
            "name": data_property_name,
            "type": data_type_name,
            "minOccurs": "0",
            "maxOccurs": "1",
        },
    )

    if is_array_schema(data_property_schema):
        item_schema = data_property_schema.get("items", {}) or {}
        add_complex_type(
            schema_element,
            data_type_name,
            item_schema,
            generated_types,
        )
    elif is_object_schema(data_property_schema):
        add_complex_type(
            schema_element,
            data_type_name,
            data_property_schema,
            generated_types,
        )
    else:
        raise ValueError(
            f"Data property '{data_property_name}' must be an object or array."
        )


def generate_oic_xsd(operation_id: str, response_schema: dict) -> str:
    response_schema = resolve_schema(response_schema)
    root_name = operation_root_name(operation_id)
    root_type_name = root_name + "Type"
    data_properties = detect_data_properties(response_schema)

    schema_element = Element(
        xs_tag("schema"),
        {
            "elementFormDefault": "unqualified",
        },
    )

    header_comment = f"""
Generated from OpenAPI specification
Operation: {operation_id}
Type: Response (Success + Error polymorphic schema)
Root element: {root_name}
    """
    add_comment_before_element(schema_element, header_comment)

    add_section_header(schema_element, "Root Element")

    SubElement(
        schema_element,
        xs_tag("element"),
        {
            "name": root_name,
            "type": root_type_name,
        },
    )

    add_section_header(schema_element, f"{root_type_name} - Root Type")

    root_type = SubElement(
        schema_element,
        xs_tag("complexType"),
        {"name": root_type_name},
    )

    root_sequence = SubElement(root_type, xs_tag("sequence"))

    add_comment_before_element(root_sequence, "Always present: SUCCESS or FAILED")
    SubElement(
        root_sequence,
        xs_tag("element"),
        {
            "name": "status",
            "type": "StatusType",
            "minOccurs": "1",
            "maxOccurs": "1",
        },
    )

    generated_types = set()

    for data_property_name, data_property_schema in data_properties:
        add_data_property_to_xsd(
            schema_element,
            root_sequence,
            data_property_name,
            data_property_schema,
            generated_types,
        )

    add_comment_before_element(
        root_sequence,
        "Filled on FAILED; maxOccurs=unbounded → serialized as JSON array",
    )
    SubElement(
        root_sequence,
        xs_tag("element"),
        {
            "name": "errors",
            "type": "ErrorItemType",
            "minOccurs": "0",
            "maxOccurs": "unbounded",
        },
    )

    add_status_type(schema_element, response_schema)
    add_error_types_from_schema(schema_element, response_schema, generated_types)

    indent_xml(schema_element)

    return tostring(
        schema_element,
        encoding="utf-8",
        xml_declaration=True,
    ).decode("utf-8")


def write_json_file(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def write_text_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        file.write(content)


def get_output_base_dir(openapi_path: Path, custom_output_dir: Path | None) -> Path:
    if custom_output_dir:
        return custom_output_dir

    folder_name = openapi_path.stem
    return Path.cwd() / "generated" / folder_name


def process_openapi(openapi_path: Path, output_base_dir: Path):
    raw_document = load_document(openapi_path)

    openapi_version = str(raw_document.get("openapi", ""))

    if not openapi_version.startswith("3."):
        raise ValueError(
            f"Expected OpenAPI 3.x document. Found: {openapi_version or 'unknown'}"
        )

    document = resolve_refs(raw_document, openapi_path)

    paths = document.get("paths", {}) or {}

    generated_results = []
    skipped_results = []

    for api_path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            method_lower = method.lower()

            if method_lower not in HTTP_METHODS:
                continue

            operation_id = operation.get("operationId")

            if not operation_id:
                skipped_results.append(
                    {
                        "path": api_path,
                        "method": method_upper(method_lower),
                        "reason": "Missing operationId",
                    }
                )
                continue

            status_code, success_response = find_success_response(operation)

            if not success_response:
                skipped_results.append(
                    {
                        "operationId": operation_id,
                        "path": api_path,
                        "method": method_upper(method_lower),
                        "reason": "No 200 or 201 success response found",
                    }
                )
                continue

            response_schema = find_json_response_schema(success_response)

            if not response_schema:
                skipped_results.append(
                    {
                        "operationId": operation_id,
                        "path": api_path,
                        "method": method_upper(method_lower),
                        "reason": "No application/json schema found on success response",
                    }
                )
                continue

            response_schema = resolve_schema(response_schema)

            operation_file_name = kebab_case(operation_id) + "-response"

            xsd_path = (
                output_base_dir
                / "schemas"
                / "response"
                / f"{operation_file_name}.xsd"
            )

            json_schema_path = (
                output_base_dir
                / "schemas"
                / "response"
                / f"{operation_file_name}.json"
            )

            xsd_content = generate_oic_xsd(operation_id, response_schema)
            write_text_file(xsd_path, xsd_content)

            write_json_file(json_schema_path, response_schema)

            result = {
                "operationId": operation_id,
                "method": method_upper(method_lower),
                "path": api_path,
                "statusCode": status_code,
                "xsdPath": xsd_path,
                "jsonSchemaPath": json_schema_path,
            }

            error_schemas = extract_error_schemas(operation)
            if error_schemas:
                merged_error_schema = merge_error_response_schemas(error_schemas)
                if merged_error_schema:
                    error_json_path = (
                        output_base_dir
                        / "schemas"
                        / "error"
                        / f"{operation_file_name}.json"
                    )
                    write_json_file(error_json_path, merged_error_schema)
                    result["errorJsonSchemaPath"] = error_json_path

            request_body = operation.get("requestBody")
            request_schema = find_json_request_schema(request_body)

            if request_schema and method_lower != "get":
                request_schema = resolve_schema(request_schema)
                operation_file_name_request = kebab_case(operation_id) + "-request"

                request_xsd_path = (
                    output_base_dir
                    / "schemas"
                    / "request"
                    / f"{operation_file_name_request}.xsd"
                )

                request_json_schema_path = (
                    output_base_dir
                    / "schemas"
                    / "request"
                    / f"{operation_file_name_request}.json"
                )

                request_xsd_content = generate_oic_request_xsd(operation_id, request_schema)
                write_text_file(request_xsd_path, request_xsd_content)
                write_json_file(request_json_schema_path, request_schema)

                result["requestXsdPath"] = request_xsd_path
                result["requestJsonSchemaPath"] = request_json_schema_path

            generated_results.append(result)

    return generated_results, skipped_results


def method_upper(method: str) -> str:
    return method.upper()


def print_results(generated_results: list[dict], skipped_results: list[dict]):
    print()

    if generated_results:
        print("Generated files:")

        for result in generated_results:
            print(f"- {result['operationId']} ({result['method']} {result['path']})")
            print(f"  Response XSD: {result['xsdPath']}")
            if "errorJsonSchemaPath" in result:
                print(f"  Error JSON Schema: {result['errorJsonSchemaPath']}")
            if "requestXsdPath" in result:
                print(f"  Request XSD:  {result['requestXsdPath']}")

    else:
        print("No files were generated.")

    if skipped_results:
        print()
        print("Skipped operations:")

        for result in skipped_results:
            operation = result.get("operationId", "unknown operation")
            method = result.get("method", "unknown method")
            path = result.get("path", "unknown path")
            reason = result.get("reason", "unknown reason")

            print(f"- {operation} ({method} {path})")
            print(f"  Reason: {reason}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate OIC Gen3 polymorphic XSD response schemas "
            "from an OpenAPI 3.x document."
        )
    )

    parser.add_argument(
        "openapi_path",
        help="Path to the OpenAPI JSON or YAML document.",
    )

    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output folder. Default: ./generated. "
            "Example: -o ./generated-partijhub"
        ),
    )

    args = parser.parse_args()

    openapi_path = Path(args.openapi_path).expanduser()

    if not openapi_path.exists():
        print(f"OpenAPI file does not exist: {openapi_path}", file=sys.stderr)
        sys.exit(1)

    output_base_dir = get_output_base_dir(
        openapi_path,
        Path(args.output).expanduser() if args.output else None,
    )

    try:
        generated_results, skipped_results = process_openapi(
            openapi_path,
            output_base_dir,
        )
    except Exception as error:
        print(f"Failed: {error}", file=sys.stderr)
        sys.exit(1)

    print_results(generated_results, skipped_results)


if __name__ == "__main__":
    main()
