from oic_generator.schema import schema_type


def infer_xs_type(schema: dict) -> str:
    """
    Map JSON Schema type and format to XSD type.
    
    Args:
        schema: JSON Schema object
        
    Returns:
        XSD type string (e.g., "xs:string", "xs:date")
    """
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
            elif current_format in ("byte", "binary"):
                if current_format == "byte" or content_encoding in ("base64", "base64url"):
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
    """Check if XSD base type supports string facets (length, pattern)."""
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
    """Check if XSD base type supports numeric facets (min, max, etc)."""
    local_name = base_type.replace("xs:", "")
    return local_name in (
        "integer",
        "int",
        "long",
        "short",
        "byte",
        "decimal",
        "float",
        "double",
        "nonNegativeInteger",
        "positiveInteger",
    )