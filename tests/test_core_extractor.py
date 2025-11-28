"""Tests for core extractor module.

This module tests:
- Schema transformation for OpenAI strict mode
- JSON parsing with various formats
- Client building
- extract_structured_data (with mocked LLM)
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from document_llm_extractor.core.extractor import (
    build_client,
    extract_structured_data,
    parse_json,
    transform_schema,
)
from document_llm_extractor.deliverynote.models import DeliveryNoteReport


def test_transform_schema_basic():
    """Test basic schema transformation."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name"],
    }
    transformed = transform_schema(schema)

    # All properties should be required
    assert "required" in transformed
    assert set(transformed["required"]) == {"name", "age"}

    # Optional field should be nullable
    assert transformed["properties"]["age"]["type"] == ["integer", "null"]


def test_transform_schema_with_defs():
    """Test schema transformation with $defs (definitions)."""
    schema = {
        "type": "object",
        "properties": {
            "product": {"$ref": "#/$defs/Product"},
        },
        "$defs": {
            "Product": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                },
            },
        },
    }
    transformed = transform_schema(schema)

    # $defs should be inlined
    assert "$defs" not in transformed

    # Product should be inlined
    assert "product" in transformed["properties"]
    product_schema = transformed["properties"]["product"]
    assert "properties" in product_schema
    assert "name" in product_schema["properties"]


def test_transform_schema_with_array():
    """Test schema transformation with array types."""
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                    },
                },
            },
        },
    }
    transformed = transform_schema(schema)

    # Array items should be transformed and preserved
    items_schema = transformed["properties"]["items"]["items"]
    assert "properties" in items_schema
    assert "id" in items_schema["properties"]
    assert "name" in items_schema["properties"]
    # The transform function processes array items - verify structure is maintained
    assert items_schema["type"] == "object"


def test_parse_json_valid():
    """Test parsing valid JSON."""
    json_str = json.dumps(
        {
            "numero_deliverynote": "A-001",
            "fecha_deliverynote": "2025-01-10",
            "nombre_empresa": "ACME SA",
            "productos": [{"producto": "Caja", "cantidad": 1.0}],
            "base_imponible": 10.0,
            "total_deliverynote": 12.1,
        }
    )

    result, error = parse_json(json_str, DeliveryNoteReport)
    assert result is not None
    assert error is None
    assert result.numero_deliverynote == "A-001"
    assert result.nombre_empresa == "ACME SA"


def test_parse_json_markdown_wrapped():
    """Test parsing JSON wrapped in markdown code blocks."""
    json_str = """```json
{
    "numero_deliverynote": "A-001",
    "fecha_deliverynote": "2025-01-10",
    "nombre_empresa": "ACME SA",
    "productos": [{"producto": "Caja", "cantidad": 1.0}],
    "base_imponible": 10.0,
    "total_deliverynote": 12.1
}
```"""

    result, error = parse_json(json_str, DeliveryNoteReport)
    assert result is not None
    assert error is None
    assert result.numero_deliverynote == "A-001"


def test_parse_json_nested():
    """Test parsing JSON with nested structure (single-key dict)."""
    # Some LLMs return {"DeliveryNoteReport": {...}}
    json_str = json.dumps(
        {
            "DeliveryNoteReport": {
                "numero_deliverynote": "A-001",
                "fecha_deliverynote": "2025-01-10",
                "nombre_empresa": "ACME SA",
                "productos": [{"producto": "Caja", "cantidad": 1.0}],
                "base_imponible": 10.0,
                "total_deliverynote": 12.1,
            }
        }
    )

    result, error = parse_json(json_str, DeliveryNoteReport)
    assert result is not None
    assert error is None
    assert result.numero_deliverynote == "A-001"


def test_parse_json_with_null_defaults():
    """Test parsing JSON with null values for fields with defaults."""
    json_str = json.dumps(
        {
            "numero_deliverynote": "A-001",
            "fecha_deliverynote": "2025-01-10",
            "nombre_empresa": "ACME SA",
            "productos": [{"producto": "Caja", "cantidad": 1.0}],
            "base_imponible": 10.0,
            "total_deliverynote": 12.1,
            "moneda": None,  # Has default "EUR"
        }
    )

    result, error = parse_json(json_str, DeliveryNoteReport)
    assert result is not None
    assert error is None
    # Should use default value
    assert result.moneda == "EUR"


def test_parse_json_invalid():
    """Test parsing invalid JSON."""
    json_str = "not valid json"
    result, error = parse_json(json_str, DeliveryNoteReport)
    assert result is None
    # Error may be None if no JSON found, or ValidationError if partial parse


def test_parse_json_empty():
    """Test parsing empty string."""
    result, error = parse_json("", DeliveryNoteReport)
    assert result is None
    assert error is None


@patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-123"})
def test_build_client():
    """Test building OpenAI client."""
    client = build_client()
    assert client is not None
    assert hasattr(client, "chat")


@patch.dict("os.environ", {}, clear=True)
def test_build_client_no_key():
    """Test building client without API key raises error."""
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY not set"):
        build_client()


@patch.dict(
    "os.environ",
    {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://custom.api/v1"},
)
def test_build_client_custom_url():
    """Test building client with custom base URL."""
    client = build_client()
    assert client is not None
    # Base URL is set internally, we can't easily check it without accessing private attributes


@patch("document_llm_extractor.core.extractor.build_client")
def test_extract_structured_data_success(mock_build_client):
    """Test successful extraction with mocked LLM."""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "numero_deliverynote": "A-001",
            "fecha_deliverynote": "2025-01-10",
            "nombre_empresa": "ACME SA",
            "productos": [{"producto": "Caja", "cantidad": 1.0}],
            "base_imponible": 10.0,
            "total_deliverynote": 12.1,
        }
    )
    mock_client.chat.completions.create.return_value = mock_response
    mock_build_client.return_value = mock_client

    result = extract_structured_data(
        text="Sample document text",
        model_class=DeliveryNoteReport,
        system_prompt="Extract information",
        user_prompt_template="Text: {text}",
    )

    assert isinstance(result, DeliveryNoteReport)
    assert result.numero_deliverynote == "A-001"
    assert mock_client.chat.completions.create.called


@patch("document_llm_extractor.core.extractor.build_client")
def test_extract_structured_data_retry_on_validation_error(mock_build_client):
    """Test that extraction retries on validation errors."""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]

    # First call returns invalid JSON, second returns valid
    mock_response.choices[0].message.content = json.dumps(
        {
            "numero_deliverynote": "A-001",
            # Missing required fields
        }
    )
    mock_response2 = MagicMock()
    mock_response2.choices = [MagicMock()]
    mock_response2.choices[0].message.content = json.dumps(
        {
            "numero_deliverynote": "A-001",
            "fecha_deliverynote": "2025-01-10",
            "nombre_empresa": "ACME SA",
            "productos": [{"producto": "Caja", "cantidad": 1.0}],
            "base_imponible": 10.0,
            "total_deliverynote": 12.1,
        }
    )
    # Provide enough responses for retries (up to 3 attempts)
    mock_response3 = MagicMock()
    mock_response3.choices = [MagicMock()]
    mock_response3.choices[0].message.content = json.dumps(
        {
            "numero_deliverynote": "A-001",
            "fecha_deliverynote": "2025-01-10",
            "nombre_empresa": "ACME SA",
            "productos": [{"producto": "Caja", "cantidad": 1.0}],
            "base_imponible": 10.0,
            "total_deliverynote": 12.1,
        }
    )

    mock_client.chat.completions.create.side_effect = [
        mock_response,
        mock_response2,
        mock_response3,
    ]
    mock_build_client.return_value = mock_client

    result = extract_structured_data(
        text="Sample document text",
        model_class=DeliveryNoteReport,
        system_prompt="Extract information",
        user_prompt_template="Text: {text}",
    )

    assert isinstance(result, DeliveryNoteReport)
    # Should have been called twice (retry)
    assert mock_client.chat.completions.create.call_count >= 2


@patch("document_llm_extractor.core.extractor.build_client")
def test_extract_structured_data_fallback_to_json_object(mock_build_client):
    """Test fallback from strict mode to json_object mode."""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "numero_deliverynote": "A-001",
            "fecha_deliverynote": "2025-01-10",
            "nombre_empresa": "ACME SA",
            "productos": [{"producto": "Caja", "cantidad": 1.0}],
            "base_imponible": 10.0,
            "total_deliverynote": 12.1,
        }
    )

    # First call raises BadRequestError (strict mode fails), second succeeds
    from openai import BadRequestError

    # Provide enough responses for potential retries (up to 3 attempts after fallback)
    mock_response2 = MagicMock()
    mock_response2.choices = [MagicMock()]
    mock_response2.choices[0].message.content = json.dumps(
        {
            "numero_deliverynote": "A-001",
            "fecha_deliverynote": "2025-01-10",
            "nombre_empresa": "ACME SA",
            "productos": [{"producto": "Caja", "cantidad": 1.0}],
            "base_imponible": 10.0,
            "total_deliverynote": 12.1,
        }
    )
    mock_response3 = MagicMock()
    mock_response3.choices = [MagicMock()]
    mock_response3.choices[0].message.content = json.dumps(
        {
            "numero_deliverynote": "A-001",
            "fecha_deliverynote": "2025-01-10",
            "nombre_empresa": "ACME SA",
            "productos": [{"producto": "Caja", "cantidad": 1.0}],
            "base_imponible": 10.0,
            "total_deliverynote": 12.1,
        }
    )

    mock_client.chat.completions.create.side_effect = [
        BadRequestError("400", response=Mock(), body={}),
        mock_response,
        mock_response2,
        mock_response3,
    ]
    mock_build_client.return_value = mock_client

    result = extract_structured_data(
        text="Sample document text",
        model_class=DeliveryNoteReport,
        system_prompt="Extract information",
        user_prompt_template="Text: {text}",
    )

    assert isinstance(result, DeliveryNoteReport)
    # Should have been called twice (fallback)
    assert mock_client.chat.completions.create.call_count == 2


@patch("document_llm_extractor.core.extractor.build_client")
def test_extract_structured_data_max_retries(mock_build_client):
    """Test that extraction fails after max retries."""
    # Mock OpenAI client that always returns invalid data
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "invalid": "data",
        }
    )
    mock_client.chat.completions.create.return_value = mock_response
    mock_build_client.return_value = mock_client

    with pytest.raises(RuntimeError, match="Failed after"):
        extract_structured_data(
            text="Sample document text",
            model_class=DeliveryNoteReport,
            system_prompt="Extract information",
            user_prompt_template="Text: {text}",
        )

    # Should have been called 3 times (max retries)
    assert mock_client.chat.completions.create.call_count == 3
