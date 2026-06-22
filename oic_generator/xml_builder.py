from xml.etree.ElementTree import Element, SubElement, Comment
from oic_generator.utils import xs_tag, pascal_case, singular_name
from oic_generator.schema import resolve_schema, is_object_schema, is_array_schema, needs_named_simple_type, build_description, is_nullable
from oic_generator.types import infer_xs_type
from oic_generator.facets import apply_schema_facets
from oic_generator.constants import SECTION_SEPARATOR_LENGTH


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
        separator = "=" * SECTION_SEPARATOR_LENGTH
        comment_text = f"\n{separator}\n{title.strip()}\n{separator}\n"
        comment = Comment(comment_text)
        parent.append(comment)




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



