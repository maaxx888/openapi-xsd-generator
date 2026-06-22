import argparse
import logging
import sys
from pathlib import Path

from oic_generator.loader import load_document, resolve_refs
from oic_generator.discovery import discover_operations, display_operations_by_tag
from oic_generator.ui import get_user_selection
from oic_generator.processor import process_openapi
from oic_generator.io import get_output_base_dir
from oic_generator.output import print_results


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate OIC Gen3 polymorphic XSD response schemas "
            "from an OpenAPI 3.x document with selective operation conversion."
        )
    )

    parser.add_argument(
        "openapi_path",
        help="Path to the OpenAPI JSON or YAML document.",
    )

    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output folder. Default: ./generated. "
            "Example: -o ./generated-partijhub"
        ),
    )

    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Convert all operations without prompting for selection (non-interactive mode).",
    )

    parser.add_argument(
        "-s",
        "--select",
        help="Comma-separated operation numbers to convert (e.g., '1,2,4'). Overrides interactive prompt.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging.",
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    openapi_path = Path(args.openapi_path).expanduser()

    if not openapi_path.exists():
        logger.error(f"OpenAPI file does not exist: {openapi_path}")
        sys.exit(1)

    output_base_dir = get_output_base_dir(
        openapi_path,
        Path(args.output).expanduser() if args.output else None,
    )

    try:
        logger.info(f"Loading OpenAPI document from {openapi_path}")
        raw_document = load_document(openapi_path)
        openapi_version = str(raw_document.get("openapi", ""))
        if not openapi_version.startswith("3."):
            raise ValueError(
                f"Expected OpenAPI 3.x document. Found: {openapi_version or 'unknown'}"
            )
        logger.debug(f"OpenAPI version: {openapi_version}")

        document = resolve_refs(raw_document, openapi_path)
        logger.info("Resolved $ref references in OpenAPI document")

        operations_info = discover_operations(document)
        if not operations_info["index_map"]:
            logger.error("No valid operations found in the OpenAPI document.")
            sys.exit(1)

        selected_operation_ids = None

        if args.all:
            selected_operation_ids = set(operations_info["index_map"].values())
            logger.info(f"Converting all {len(selected_operation_ids)} operations...")
        elif args.select:
            try:
                selected_indices = set()
                for part in args.select.split(","):
                    part = part.strip()
                    if part:
                        idx = int(part)
                        if idx not in operations_info["index_map"]:
                            logger.error(f"Invalid operation number: {idx}")
                            sys.exit(1)
                        selected_indices.add(idx)
                selected_operation_ids = {
                    operations_info["index_map"][idx] for idx in selected_indices
                }
                logger.info(f"Converting {len(selected_operation_ids)} selected operations...")
            except ValueError:
                logger.error("--select must contain valid numbers separated by commas.")
                sys.exit(1)
        else:
            display_operations_by_tag(operations_info)
            selected_operation_ids = get_user_selection(operations_info)
            logger.info(f"User selected {len(selected_operation_ids)} operations")

        generated_results, skipped_results = process_openapi(
            openapi_path,
            output_base_dir,
            selected_operation_ids,
        )
        logger.info("Processing completed successfully")

    except Exception as error:
        logger.error(f"Failed: {error}")
        sys.exit(1)

    print_results(generated_results, skipped_results)


if __name__ == "__main__":
    main()
