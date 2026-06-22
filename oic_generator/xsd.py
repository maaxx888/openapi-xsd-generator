from xml.etree.ElementTree import Element, SubElement, tostring
from oic_generator.utils import kebab_case, pascal_case, xs_tag
from oic_generator.xml_builder import indent_xml, add_comment_before_element, add_section_header, add_property_element, add_complex_type, add_status_type, add_error_types_from_schema, add_fallback_error_types
from oic_generator.schema import is_object_schema, is_array_schema, resolve_schema
from oic_generator.operations import detect_envelope_fields, operation_root_name, detect_data_properties
from oic_generator.types import infer_xs_type


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

    envelope_fields = detect_envelope_fields(response_schema)
    for envelope_field_name, envelope_field_schema in envelope_fields:
        xs_type = infer_xs_type(envelope_field_schema)
        description = envelope_field_schema.get("description")
        if description:
            add_comment_before_element(root_sequence, description)
        SubElement(
            root_sequence,
            xs_tag("element"),
            {
                "name": envelope_field_name,
                "type": xs_type,
                "minOccurs": "0",
                "maxOccurs": "1",
            },
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



