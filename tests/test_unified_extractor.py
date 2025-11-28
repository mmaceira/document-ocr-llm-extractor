"""Tests for unified extractor module.

This module tests:
- extract_document function for all document types
- Text limit handling
- Error handling for invalid document types
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from document_llm_extractor.bank.models import BankStatement
from document_llm_extractor.deliverynote.models import DeliveryNoteReport, ProductoLinea
from document_llm_extractor.payroll.models import PayrollReport
from document_llm_extractor.unified_extractor import extract_document


@patch("document_llm_extractor.unified_extractor.extract_structured_data")
def test_extract_document_albaran(mock_extract):
    """Test extract_document for albaran type."""
    expected_report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=[ProductoLinea(producto="Caja", cantidad=1.0)],
        base_imponible=10.0,
        total_deliverynote=12.1,
    )
    mock_extract.return_value = expected_report

    result = extract_document("deliverynote", "Sample delivery note text")

    assert isinstance(result, DeliveryNoteReport)
    assert result.numero_deliverynote == "A-001"
    mock_extract.assert_called_once()
    # Check that correct model class and prompts were used
    call_args = mock_extract.call_args
    assert call_args.kwargs["model_class"] == DeliveryNoteReport


@patch("document_llm_extractor.unified_extractor.extract_structured_data")
def test_extract_document_bank(mock_extract):
    """Test extract_document for bank type."""
    expected_statement = BankStatement(
        banco="Banco Popular",
        lineas=[],
    )
    mock_extract.return_value = expected_statement

    result = extract_document("bank", "Sample bank statement text")

    assert isinstance(result, BankStatement)
    assert result.banco == "Banco Popular"
    mock_extract.assert_called_once()


@patch("document_llm_extractor.unified_extractor.extract_structured_data")
def test_extract_document_payroll(mock_extract):
    """Test extract_document for payroll type."""
    expected_report = PayrollReport(
        empresa_nif="B12345678",
        devengos=[],
        deducciones=[],
    )
    mock_extract.return_value = expected_report

    result = extract_document("payroll", "Sample payroll text")

    assert isinstance(result, PayrollReport)
    assert result.empresa_nif == "B12345678"
    mock_extract.assert_called_once()


def test_extract_document_invalid_type():
    """Test extract_document with invalid document type."""
    with pytest.raises(ValueError, match="Unknown doc_type"):
        extract_document("invalid_type", "Some text")


@patch("document_llm_extractor.unified_extractor.extract_structured_data")
def test_extract_document_text_limit(mock_extract):
    """Test that text limit is applied for document types with limits."""
    expected_report = BankStatement(lineas=[])
    mock_extract.return_value = expected_report

    # Create text longer than 40000 characters (bank's limit)
    long_text = "A" * 50000

    extract_document("bank", long_text)

    # Check that text was truncated
    call_args = mock_extract.call_args
    passed_text = call_args.kwargs["text"]
    assert len(passed_text) == 40000
    assert passed_text == "A" * 40000


@patch("document_llm_extractor.unified_extractor.extract_structured_data")
def test_extract_document_no_text_limit(mock_extract):
    """Test that text limit is not applied when None."""
    expected_report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=[ProductoLinea(producto="Caja", cantidad=1.0)],
        base_imponible=10.0,
        total_deliverynote=12.1,
    )
    mock_extract.return_value = expected_report

    # Create text longer than typical limit
    long_text = "A" * 50000

    extract_document("deliverynote", long_text)

    # Check that text was NOT truncated (albaran has no limit)
    call_args = mock_extract.call_args
    passed_text = call_args.kwargs["text"]
    assert len(passed_text) == 50000


@patch("document_llm_extractor.unified_extractor.extract_structured_data")
def test_extract_document_with_model_override(mock_extract):
    """Test extract_document with model override."""
    expected_report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=[ProductoLinea(producto="Caja", cantidad=1.0)],
        base_imponible=10.0,
        total_deliverynote=12.1,
    )
    mock_extract.return_value = expected_report

    extract_document("deliverynote", "Sample text", model="gpt-4")

    call_args = mock_extract.call_args
    assert call_args.kwargs["model"] == "gpt-4"


@patch("document_llm_extractor.unified_extractor.extract_structured_data")
def test_extract_document_with_debug_dir(mock_extract):
    """Test extract_document with debug directory."""
    expected_report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=[ProductoLinea(producto="Caja", cantidad=1.0)],
        base_imponible=10.0,
        total_deliverynote=12.1,
    )
    mock_extract.return_value = expected_report

    debug_dir = Path("/tmp/debug")
    extract_document("deliverynote", "Sample text", debug_dir=debug_dir)

    call_args = mock_extract.call_args
    assert call_args.kwargs["debug_dir"] == debug_dir


@patch("document_llm_extractor.unified_extractor.extract_structured_data")
def test_extract_document_text_limit_exact(mock_extract):
    """Test text limit when text is exactly at the limit."""
    expected_report = BankStatement(lineas=[])
    mock_extract.return_value = expected_report

    # Create text exactly at 40000 characters
    exact_text = "A" * 40000

    extract_document("bank", exact_text)

    # Text should not be truncated
    call_args = mock_extract.call_args
    passed_text = call_args.kwargs["text"]
    assert len(passed_text) == 40000


@patch("document_llm_extractor.unified_extractor.extract_structured_data")
def test_extract_document_text_limit_one_over(mock_extract):
    """Test text limit when text is one character over the limit."""
    expected_report = BankStatement(lineas=[])
    mock_extract.return_value = expected_report

    # Create text one character over 40000
    over_text = "A" * 40001

    extract_document("bank", over_text)

    # Text should be truncated to 40000
    call_args = mock_extract.call_args
    passed_text = call_args.kwargs["text"]
    assert len(passed_text) == 40000
