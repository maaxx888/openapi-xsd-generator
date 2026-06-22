from oic_generator.constants import HTTP_METHODS
from oic_generator.utils import pascal_case


def method_upper(method: str) -> str:
    return method.upper()


def discover_operations(document: dict) -> dict:
    paths = document.get("paths", {}) or {}
    operations_by_tag = {}
    index_to_operation = {}
    current_index = 1

    for api_path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            method_lower = method.lower()

            if method_lower not in HTTP_METHODS:
                continue

            operation_id = operation.get("operationId")
            if not operation_id:
                continue

            tags = operation.get("tags", ["Untagged"])
            if not tags:
                tags = ["Untagged"]

            for tag in tags:
                if tag not in operations_by_tag:
                    operations_by_tag[tag] = []

                operation_info = {
                    "operationId": operation_id,
                    "method": method_upper(method_lower),
                    "path": api_path,
                    "index": current_index,
                    "tag": tag,
                }

                operations_by_tag[tag].append(operation_info)
                index_to_operation[current_index] = operation_id

                current_index += 1

    return {
        "by_tag": operations_by_tag,
        "index_map": index_to_operation,
    }


def display_operations_by_tag(operations_info: dict) -> None:
    print("\n" + "=" * 80)
    print("AVAILABLE APIS AND OPERATIONS")
    print("=" * 80 + "\n")

    operations_by_tag = operations_info["by_tag"]

    for tag in sorted(operations_by_tag.keys()):
        print(f"{tag}:")
        for op in operations_by_tag[tag]:
            print(f"  {op['index']}. {op['operationId']} ({op['method']} {op['path']})")
        print()
