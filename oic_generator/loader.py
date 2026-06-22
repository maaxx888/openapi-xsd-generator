import json
import logging
from pathlib import Path
import yaml
import jsonref

logger = logging.getLogger(__name__)


def load_document(path: Path) -> dict:
    """
    Load OpenAPI document from JSON or YAML file.
    
    Args:
        path: Path to OpenAPI file
        
    Returns:
        Parsed OpenAPI document dict
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"OpenAPI file not found: {path}")
    
    try:
        with path.open("r", encoding="utf-8") as file:
            if path.suffix.lower() in [".yaml", ".yml"]:
                doc = yaml.safe_load(file)
            else:
                doc = json.load(file)
            
            if not isinstance(doc, dict):
                raise ValueError("OpenAPI document must be a JSON/YAML object")
            
            logger.info(f"Loaded OpenAPI document from {path}")
            return doc
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {path}: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load {path}: {e}")


def resolve_refs(document: dict, source_path: Path) -> dict:
    """
    Resolve all JSON references ($ref) in OpenAPI document.
    
    Args:
        document: OpenAPI document with potential references
        source_path: Path to OpenAPI file (for resolving relative refs)
        
    Returns:
        Document with all references resolved
    """
    try:
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

        result = convert_to_dict(resolved)
        logger.info("Successfully resolved all references")
        return result
        
    except Exception as e:
        logger.error(f"Failed to resolve references: {e}")
        raise ValueError(f"Reference resolution failed: {e}")