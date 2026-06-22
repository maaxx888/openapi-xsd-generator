from pathlib import Path
from oic_generator.loader import load_document, resolve_refs
from oic_generator.constants import HTTP_METHODS
from oic_generator.operations import find_success_response, find_json_response_schema, extract_error_schemas, merge_error_response_schemas, merge_response_schemas_with_errors, find_json_request_schema
from oic_generator.schema import resolve_schema
from oic_generator.xsd import generate_oic_xsd, generate_oic_request_xsd
from oic_generator.io import write_text_file, write_json_file
from oic_generator.utils import kebab_case
from oic_generator.discovery import method_upper


def process_openapi(openapi_path: Path, output_base_dir: Path, selected_operation_ids: set[str] | None = None):
     raw_document = load_document(openapi_path)

     openapi_version = str(raw_document.get("openapi", ""))

     if not openapi_version.startswith("3."):
         raise ValueError(
             f"Expected OpenAPI 3.x document. Found: {openapi_version or 'unknown'}"
         )

     document = resolve_refs(raw_document, openapi_path)

     paths = document.get("paths", {}) or {}

     generated_results = []
     skipped_results = []

     for api_path, path_item in paths.items():
         if not isinstance(path_item, dict):
             continue

         for method, operation in path_item.items():
             method_lower = method.lower()

             if method_lower not in HTTP_METHODS:
                 continue

             operation_id = operation.get("operationId")

             if not operation_id:
                 skipped_results.append(
                     {
                         "path": api_path,
                         "method": method_upper(method_lower),
                         "reason": "Missing operationId",
                     }
                 )
                 continue

             if selected_operation_ids and operation_id not in selected_operation_ids:
                 continue

             status_code, success_response = find_success_response(operation)

             if not success_response:
                 skipped_results.append(
                     {
                         "operationId": operation_id,
                         "path": api_path,
                         "method": method_upper(method_lower),
                         "reason": "No 200 or 201 success response found",
                     }
                 )
                 continue

             response_schema = find_json_response_schema(success_response)

             if not response_schema:
                 skipped_results.append(
                     {
                         "operationId": operation_id,
                         "path": api_path,
                         "method": method_upper(method_lower),
                         "reason": "No application/json schema found on success response",
                     }
                 )
                 continue

             response_schema = resolve_schema(response_schema)

             merged_response_schema = merge_response_schemas_with_errors(operation)
             if not merged_response_schema:
                 merged_response_schema = response_schema

             operation_file_name = kebab_case(operation_id) + "-response"

             xsd_path = (
                 output_base_dir
                 / "schemas"
                 / "response"
                 / f"{operation_file_name}.xsd"
             )

             json_schema_path = (
                 output_base_dir
                 / "schemas"
                 / "response"
                 / f"{operation_file_name}.json"
             )

             xsd_content = generate_oic_xsd(operation_id, merged_response_schema)
             write_text_file(xsd_path, xsd_content)

             write_json_file(json_schema_path, response_schema)

             result = {
                 "operationId": operation_id,
                 "method": method_upper(method_lower),
                 "path": api_path,
                 "statusCode": status_code,
                 "xsdPath": xsd_path,
                 "jsonSchemaPath": json_schema_path,
             }

             error_schemas = extract_error_schemas(operation)
             if error_schemas:
                 merged_error_schema = merge_error_response_schemas(error_schemas)
                 if merged_error_schema:
                     error_json_path = (
                         output_base_dir
                         / "schemas"
                         / "error"
                         / f"{kebab_case(operation_id)}-error-response.json"
                     )
                     write_json_file(error_json_path, merged_error_schema)
                     result["errorJsonSchemaPath"] = error_json_path

             request_body = operation.get("requestBody")
             request_schema = find_json_request_schema(request_body)

             if request_schema and method_lower != "get":
                 request_schema = resolve_schema(request_schema)
                 operation_file_name_request = kebab_case(operation_id) + "-request"

                 request_xsd_path = (
                     output_base_dir
                     / "schemas"
                     / "request"
                     / f"{operation_file_name_request}.xsd"
                 )

                 request_json_schema_path = (
                     output_base_dir
                     / "schemas"
                     / "request"
                     / f"{operation_file_name_request}.json"
                 )

                 request_xsd_content = generate_oic_request_xsd(operation_id, request_schema)
                 write_text_file(request_xsd_path, request_xsd_content)
                 write_json_file(request_json_schema_path, request_schema)

                 result["requestXsdPath"] = request_xsd_path
                 result["requestJsonSchemaPath"] = request_json_schema_path

             generated_results.append(result)

     return generated_results, skipped_results

