import re
from oic_generator.constants import XS_NS


def pascal_case(value: str) -> str:
    """
    Convert string to PascalCase.
    
    Examples:
        "hello_world" -> "HelloWorld"
        "helloWorld" -> "HelloWorld"
    """
    value = value.replace("_", "-")
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value)
    parts = re.split(r"[^A-Za-z0-9]+", value)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def kebab_case(value: str) -> str:
    """
    Convert string to kebab-case.
    
    Examples:
        "helloWorld" -> "hello-world"
        "Hello_World" -> "hello-world"
    """
    value = value.replace("_", "-")
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value)
    value = re.sub(r"[^A-Za-z0-9]+", "-", value)
    return value.strip("-").lower()


def singular_name(value: str) -> str:
    """
    Convert plural names to singular form.
    
    Examples:
        "users" -> "user"
        "entries" -> "entry"
        "addresses" -> "addresse"
    """
    if value.endswith("ies"):
        return value[:-3] + "y"

    if value.endswith("ses"):
        return value[:-2]

    if value.endswith("s") and not value.endswith("ss"):
        return value[:-1]

    return value


def xs_tag(local_name: str) -> str:
    """
    Create XML Schema namespace tag.
    
    Args:
        local_name: Element name (e.g., "element", "complexType")
        
    Returns:
        Fully qualified XML Schema tag
    """
    return f"{{{XS_NS}}}{local_name}"