import copy
from oic_generator.constants import FACET_KEYS


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
