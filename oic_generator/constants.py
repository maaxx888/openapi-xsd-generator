from xml.etree.ElementTree import register_namespace

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

SECTION_SEPARATOR_LENGTH = 80

