from xml.etree.ElementTree import Element, SubElement
from oic_generator.utils import xs_tag
from oic_generator.types import xs_base_supports_string_facets, xs_base_supports_numeric_facets


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
        from oic_generator.xml_builder import add_comment_before_element
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
