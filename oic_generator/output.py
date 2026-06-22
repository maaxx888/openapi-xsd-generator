def print_results(generated_results: list[dict], skipped_results: list[dict]):
    print()

    if generated_results:
        print("Generated files:")

        for result in generated_results:
            print(f"- {result['operationId']} ({result['method']} {result['path']})")
            print(f"  Response XSD: {result['xsdPath']}")
            if "errorJsonSchemaPath" in result:
                print(f"  Error JSON Schema: {result['errorJsonSchemaPath']}")
            if "requestXsdPath" in result:
                print(f"  Request XSD:  {result['requestXsdPath']}")

    else:
        print("No files were generated.")

    if skipped_results:
        print()
        print("Skipped operations:")

        for result in skipped_results:
            operation = result.get("operationId", "unknown operation")
            method = result.get("method", "unknown method")
            path = result.get("path", "unknown path")
            reason = result.get("reason", "unknown reason")

            print(f"- {operation} ({method} {path})")
            print(f"  Reason: {reason}")
