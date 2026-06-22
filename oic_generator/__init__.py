from oic_generator.loader import load_document, resolve_refs
from oic_generator.processor import process_openapi
from oic_generator.discovery import discover_operations
from oic_generator.ui import get_user_selection
from oic_generator.io import get_output_base_dir

__version__ = "1.0.0"
__all__ = [
    "load_document",
    "resolve_refs",
    "process_openapi",
    "discover_operations",
    "get_user_selection",
    "get_output_base_dir",
]
