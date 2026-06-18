"""Tests for OpenAPI → XSD / JSON schema generation."""

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from oic_xsd_gen import (
    deep_merge_schemas,
    generate_oic_request_xsd,
    generate_oic_xsd,
    infer_xs_type,
    process_openapi,
    resolve_schema,
)

ROOT = Path(__file__).resolve().parent.parent
TEST_INPUT = ROOT / "test-input"


def xsd_text(operation_id: str, schema: dict) -> str:
    return generate_oic_xsd(operation_id, schema)


def request_xsd_text(operation_id: str, schema: dict) -> str:
    return generate_oic_request_xsd(operation_id, schema)


class TestInferXsType:
    def test_byte_defaults_to_base64(self):
        assert infer_xs_type({"type": "string", "format": "byte"}) == "xs:base64Binary"

    def test_date_formats(self):
        assert infer_xs_type({"type": "string", "format": "date"}) == "xs:date"
        assert infer_xs_type({"type": "string", "format": "date-time"}) == "xs:dateTime"


class TestResolveSchema:
    def test_all_of_merges_properties(self):
        schema = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"a": {"type": "string"}},
                    "required": ["a"],
                },
                {
                    "type": "object",
                    "properties": {"b": {"type": "integer"}},
                    "required": ["b"],
                },
            ]
        }
        resolved = resolve_schema(schema)
        assert "a" in resolved["properties"]
        assert "b" in resolved["properties"]
        assert "a" in resolved["required"]
        assert "b" in resolved["required"]

    def test_one_of_merges_object_branches(self):
        schema = {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {"x": {"type": "string"}},
                },
                {
                    "type": "object",
                    "properties": {"y": {"type": "string"}},
                },
            ]
        }
        resolved = resolve_schema(schema)
        assert "x" in resolved["properties"]
        assert "y" in resolved["properties"]


class TestDeepMergeSchemas:
    def test_nested_property_merge(self):
        base = {
            "type": "object",
            "properties": {
                "errors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"code": {"type": "string"}},
                    },
                }
            },
        }
        overlay = {
            "type": "object",
            "properties": {
                "errors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "details": {
                                "type": "object",
                                "properties": {"field": {"type": "string"}},
                            }
                        },
                    },
                },
                "correlationId": {"type": "string", "format": "uuid"},
            },
        }
        merged = deep_merge_schemas(base, overlay)
        error_items = merged["properties"]["errors"]["items"]["properties"]
        assert "code" in error_items
        assert "details" in error_items
        assert "correlationId" in merged["properties"]


class TestComprehensiveTypes:
  @pytest.fixture
  def xsd(self):
      spec_path = TEST_INPUT / "comprehensive-types-api-v1.0.0.json"
      _, skipped = process_openapi(spec_path, ROOT / "generated" / "test-comprehensive")
      assert not skipped
      xsd_path = (
          ROOT
          / "generated"
          / "test-comprehensive"
          / "schemas"
          / "request"
          / "test-comprehensive-types-request.xsd"
      )
      return xsd_path.read_text(encoding="utf-8")

  def test_type_mappings(self, xsd):
      expectations = {
          "dateField": "xs:date",
          "dateTimeField": "xs:dateTime",
          "timeField": "xs:time",
          "durationField": "xs:duration",
          "int32Field": "xs:int",
          "int64Field": "xs:long",
          "floatField": "xs:float",
          "doubleField": "xs:double",
          "decimalField": "xs:decimal",
          "booleanField": "xs:boolean",
          "base64Field": "xs:base64Binary",
      }
      for field, xs_type in expectations.items():
          assert re.search(
              rf'name="{field}" type="{xs_type}"',
              xsd,
          ), f"Expected {field} → {xs_type}"


class TestConstraintsApi:
  @pytest.fixture
  def artifacts(self):
      spec_path = TEST_INPUT / "constraints-api-v1.0.0.json"
      generated, skipped = process_openapi(
          spec_path,
          ROOT / "generated" / "test-constraints",
      )
      assert len(generated) == 2
      assert not skipped
      return generated

  def test_string_constraints_in_response_xsd(self, artifacts):
      response_xsd = Path(artifacts[0]["xsdPath"]).read_text(encoding="utf-8")
      assert "maxLength" in response_xsd
      assert "minLength" in response_xsd
      assert "pattern" in response_xsd

  def test_all_of_fields_in_response_xsd(self, artifacts):
      response_xsd = Path(artifacts[0]["xsdPath"]).read_text(encoding="utf-8")
      assert "registrationNumber" in response_xsd
      assert "sector" in response_xsd
      assert "verified" in response_xsd

  def test_one_of_merged_in_request_xsd(self, artifacts):
      request_xsd = Path(artifacts[1]["requestXsdPath"]).read_text(encoding="utf-8")
      assert "foreignId" in request_xsd
      assert "registrationNumber" in request_xsd

  def test_dynamic_error_schema(self, artifacts):
      response_xsd = Path(artifacts[0]["xsdPath"]).read_text(encoding="utf-8")
      assert "ErrorItemType" in response_xsd
      assert "field" in response_xsd
      assert "reason" in response_xsd

  def test_merged_json_includes_correlation_id(self, artifacts):
      json_path = Path(artifacts[0]["jsonSchemaPath"])
      schema = json.loads(json_path.read_text(encoding="utf-8"))
      assert "correlationId" in schema["properties"]

  def test_xsd_is_well_formed(self, artifacts):
      for artifact in artifacts:
          ET.parse(artifact["xsdPath"])


class TestPartijhub:
  def test_generates_without_skip(self):
      spec_path = TEST_INPUT / "partijhub-api-v1.0.0.json"
      generated, skipped = process_openapi(
          spec_path,
          ROOT / "generated" / "test-partijhub",
      )
      assert len(generated) == 1
      assert not skipped
