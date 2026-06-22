import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def write_json_file(path: Path, data: dict):
    """
    Write JSON data to file with formatting.
    
    Args:
        path: Target file path
        data: Dictionary to write
        
    Raises:
        OSError: If write fails
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Wrote JSON file: {path}")
    except OSError as e:
        logger.error(f"Failed to write JSON to {path}: {e}")
        raise


def write_text_file(path: Path, content: str):
    """
    Write text/XSD content to file.
    
    Args:
        path: Target file path
        content: Text content to write
        
    Raises:
        OSError: If write fails
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(content)
        logger.debug(f"Wrote text file: {path}")
    except OSError as e:
        logger.error(f"Failed to write text to {path}: {e}")
        raise


def get_output_base_dir(openapi_path: Path, custom_output_dir: Path | None) -> Path:
    """
    Determine output directory for generated files.
    
    Args:
        openapi_path: Path to source OpenAPI document
        custom_output_dir: Optional custom output directory
        
    Returns:
        Output directory path
    """
    if custom_output_dir:
        return custom_output_dir

    stem = openapi_path.stem
    return Path("./generated") / stem