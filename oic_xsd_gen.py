#!/usr/bin/env python3

import argparse
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


def schema_type(schema: dict):
    value = schema.get("type")

    if isinstance(value, list):
        non_null_values = [item for item in value if item != "null"]
        if non_null_values:
            return non_null_values[0]
        return "string"

    return value


def is_object_schema(schema: dict) -> bool:
    return schema_type(schema) == "object" or "properties" in schema


def is_array_schema(schema: dict) -> bool:
    return schema_type(schema) == "array"


def infer_xs_type(schema: dict) -> str:
    current_type = schema_type(schema)
    current_format = schema.get("format")

    if current_type == "string":
        # For OIC JSON serialization, xs:string is safest for dates.
        # OIC will still output JSON strings.
        return "xs:string"

    if current_type == "integer":
        if current_format == "int64":
            return "xs:long"
        return "xs:int"

    if current_type == "number":
        return "xs:decimal"

    if current_type == "boolean":
        return "xs:boolean"

    return "xs:string"


def add_status_type(schema_element: Element):
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

    add_comment_before_element(restriction, "Operation succeeded")
    SubElement(
        restriction,
        xs_tag("enumeration"),
        {"value": "SUCCESS"},
    )

    add_comment_before_element(restriction, "Operation failed")
    SubElement(
        restriction,
        xs_tag("enumeration"),
        {"value": "FAILED"},
    )


def add_error_types(schema_element: Element):
    details_type = SubElement(
        schema_element,
        xs_tag("complexType"),
        {"name": "ErrorDetailsType"},
    )

    details_sequence = SubElement(details_type, xs_tag("sequence"))

    add_comment_before_element(details_sequence, "Error identification code")
    SubElement(
        details_sequence,
        xs_tag("element"),
        {
            "name": "identification",
            "type": "xs:string",
            "minOccurs": "0",
            "maxOccurs": "1",
        },
    )

    add_comment_before_element(details_sequence, "Error diagnostic message")
    SubElement(
        details_sequence,
        xs_tag("element"),
        {
            "name": "diagnose",
            "type": "xs:string",
            "minOccurs": "0",
            "maxOccurs": "1",
        },
    )

    error_type = SubElement(
        schema_element,
        xs_tag("complexType"),
        {"name": "ErrorItemType"},
    )

    error_sequence = SubElement(error_type, xs_tag("sequence"))

    add_comment_before_element(error_sequence, "Machine-readable error code")
    SubElement(
        error_sequence,
        xs_tag("element"),
        {
            "name": "code",
            "type": "xs:string",
            "minOccurs": "1",
            "maxOccurs": "1",
        },
    )

    add_comment_before_element(error_sequence, "Human-readable error message")
    SubElement(
        error_sequence,
        xs_tag("element"),
        {
            "name": "message",
            "type": "xs:string",
            "minOccurs": "1",
            "maxOccurs": "1",
        },
    )

    add_comment_before_element(error_sequence, "Error details (backend-specific)")
    SubElement(
        error_sequence,
        xs_tag("element"),
        {
            "name": "details",
            "type": "ErrorDetailsType",
            "minOccurs": "0",
            "maxOccurs": "1",
        },
    )


def add_enum_simple_type(schema_element: Element, type_name: str, values: list[str], generated_types: set[str]):
    if type_name in generated_types:
        return

    generated_types.add(type_name)

    simple_type = SubElement(
        schema_element,
        xs_tag("simpleType"),
        {"name": type_name},
    )

    restriction = SubElement(
        simple_type,
        xs_tag("restriction"),
        {"base": "xs:string"},
    )

    for value in values:
        SubElement(
            restriction,
            xs_tag("enumeration"),
            {"value": str(value)},
        )


def add_complex_type(
    schema_element: Element,
    type_name: str,
    json_schema: dict,
    generated_types: set[str],
):
    if type_name in generated_types:
        return

    generated_types.add(type_name)

    complex_type = SubElement(
        schema_element,
        xs_tag("complexType"),
        {"name": type_name},
    )

    sequence = SubElement(complex_type, xs_tag("sequence"))

    properties = json_schema.get("properties", {}) or {}
    required = set(json_schema.get("required", []) or [])

    for property_name, property_schema in properties.items():
        if property_name in ["status", "errors"]:
            continue

        min_occurs = "1" if property_name in required else "0"
        
        description = property_schema.get("description", "")

        if is_array_schema(property_schema):
            item_schema = property_schema.get("items", {}) or {}

            if is_object_schema(item_schema):
                base_name = singular_name(property_name)
                item_type_name = pascal_case(base_name) + "ItemType"

                add_complex_type(
                    schema_element,
                    item_type_name,
                    item_schema,
                    generated_types,
                )

                element_type = item_type_name
            elif "enum" in item_schema:
                enum_type_name = pascal_case(singular_name(property_name)) + "Type"

                add_enum_simple_type(
                    schema_element,
                    enum_type_name,
                    item_schema["enum"],
                    generated_types,
                )

                element_type = enum_type_name
            else:
                element_type = infer_xs_type(item_schema)

            add_comment_before_element(sequence, description)
            SubElement(
                sequence,
                xs_tag("element"),
                {
                    "name": property_name,
                    "type": element_type,
                    "minOccurs": min_occurs,
                    "maxOccurs": "unbounded",
                },
            )

            continue

        if is_object_schema(property_schema):
            child_type_name = pascal_case(property_name) + "Type"

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
                    "minOccurs": min_occurs,
                    "maxOccurs": "1",
                },
            )

            continue

        if "enum" in property_schema:
            enum_type_name = pascal_case(property_name) + "Type"

            add_enum_simple_type(
                schema_element,
                enum_type_name,
                property_schema["enum"],
                generated_types,
            )

            element_type = enum_type_name
        else:
            element_type = infer_xs_type(property_schema)

        add_comment_before_element(sequence, description)
        SubElement(
            sequence,
            xs_tag("element"),
            {
                "name": property_name,
                "type": element_type,
                "minOccurs": min_occurs,
                "maxOccurs": "1",
            },
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


def find_success_response(operation: dict) -> tuple[str, dict] | tuple[None, None]:
    responses = operation.get("responses", {}) or {}

    for status_code in ["200", "201"]:
        if status_code in responses:
            return status_code, responses[status_code]

    return None, None


def detect_data_property(response_schema: dict) -> tuple[str, dict] | tuple[None, None]:
    properties = response_schema.get("properties", {}) or {}

    ignored_properties = {"status", "errors"}

    for property_name, property_schema in properties.items():
        if property_name not in ignored_properties:
            return property_name, property_schema

    return None, None


def operation_root_name(operation_id: str) -> str:
    name = pascal_case(operation_id)

    if name.endswith("Response"):
        return name

    return name + "Response"


def generate_oic_request_xsd(operation_id: str, request_schema: dict) -> str:
    root_name = pascal_case(operation_id) + "Request"
    root_type_name = root_name + "Type"

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
        simple_type = SubElement(
            schema_element,
            xs_tag("simpleType"),
            {"name": root_type_name},
        )
        restriction = SubElement(
            simple_type,
            xs_tag("restriction"),
            {"base": infer_xs_type(request_schema)},
        )

    indent_xml(schema_element)

    return tostring(
        schema_element,
        encoding="utf-8",
        xml_declaration=True,
    ).decode("utf-8")


def generate_oic_xsd(operation_id: str, response_schema: dict) -> str:
    root_name = operation_root_name(operation_id)
    root_type_name = root_name + "Type"

    data_property_name, data_property_schema = detect_data_property(response_schema)

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

    if data_property_name is not None:
        data_type_name = pascal_case(data_property_name) + "ResponseType"

        add_comment_before_element(root_sequence, f"Filled on SUCCESS (from {data_property_name})")
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

    add_comment_before_element(root_sequence, "Filled on FAILED; maxOccurs=unbounded → serialized as JSON array")
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

    add_status_type(schema_element)
    add_error_types(schema_element)

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

            operation_file_name = kebab_case(operation_id) + "-response"

            json_schema_path = (
                output_base_dir
                / "schemas"
                / "json"
                / f"{operation_file_name}.schema.json"
            )

            xsd_path = (
                output_base_dir
                / "schemas"
                / "response"
                / f"{operation_file_name}.xsd"
            )

            write_json_file(json_schema_path, response_schema)

            xsd_content = generate_oic_xsd(operation_id, response_schema)
            write_text_file(xsd_path, xsd_content)

            result = {
                "operationId": operation_id,
                "method": method_upper(method_lower),
                "path": api_path,
                "statusCode": status_code,
                "jsonSchemaPath": json_schema_path,
                "xsdPath": xsd_path,
            }

            request_body = operation.get("requestBody")
            request_schema = find_json_request_schema(request_body)

            if request_schema and method_lower != "get":
                operation_file_name_request = kebab_case(operation_id) + "-request"

                request_json_schema_path = (
                    output_base_dir
                    / "schemas"
                    / "json"
                    / f"{operation_file_name_request}.schema.json"
                )

                request_xsd_path = (
                    output_base_dir
                    / "schemas"
                    / "request"
                    / f"{operation_file_name_request}.xsd"
                )

                write_json_file(request_json_schema_path, request_schema)
                request_xsd_content = generate_oic_request_xsd(operation_id, request_schema)
                write_text_file(request_xsd_path, request_xsd_content)

                result["requestJsonSchemaPath"] = request_json_schema_path
                result["requestXsdPath"] = request_xsd_path

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
