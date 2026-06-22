from oic_generator.schema import resolve_schema, schema_type, deep_merge_schemas
from oic_generator.constants import HTTP_METHODS
from oic_generator.utils import pascal_case


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

    data_properties = []
    for property_name, property_schema in properties.items():
        if property_name in ignored_properties:
            continue
        prop_type = schema_type(property_schema)
        if prop_type in ("object", "array"):
            data_properties.append((property_name, property_schema))

    return data_properties


def detect_envelope_fields(response_schema: dict) -> list[tuple[str, dict]]:
    properties = response_schema.get("properties", {}) or {}
    ignored_properties = {"status", "errors"}

    envelope_fields = []
    for property_name, property_schema in properties.items():
        if property_name in ignored_properties:
            continue
        prop_type = schema_type(property_schema)
        if prop_type not in ("object", "array"):
            envelope_fields.append((property_name, property_schema))

    return envelope_fields


def operation_root_name(operation_id: str) -> str:
    name = pascal_case(operation_id)

    if name.endswith("Response"):
        return name

    return name + "Response"



