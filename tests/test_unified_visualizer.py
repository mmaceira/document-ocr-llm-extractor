"""Tests for unified visualizer module.

This module tests:
- annotate_document_pdf for all document types
- Legend generation integration
- Redaction handling
- Error handling
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from document_llm_extractor.bank.models import BankStatement
from document_llm_extractor.deliverynote.models import DeliveryNoteReport, ProductoLinea
from document_llm_extractor.payroll.models import PayrollReport
from document_llm_extractor.unified_visualizer import annotate_document_pdf


def test_annotate_document_pdf_invalid_type(tmp_path):
    """Test annotate_document_pdf with invalid document type."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    output_pdf = tmp_path / "output.pdf"

    report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=[ProductoLinea(producto="Caja", cantidad=1.0)],
        base_imponible=10.0,
        total_deliverynote=12.1,
    )

    with pytest.raises(ValueError, match="Unknown doc_type"):
        annotate_document_pdf(
            doc_type="invalid_type",
            input_pdf=pdf_file,
            report=report,
            ocr_items=[],
            output_pdf=output_pdf,
        )


@patch("document_llm_extractor.unified_visualizer.annotate_pdf")
def test_annotate_document_pdf_albaran(mock_annotate, tmp_path):
    """Test annotate_document_pdf for albaran type."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    output_pdf = tmp_path / "output.pdf"

    report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=[ProductoLinea(producto="Caja", cantidad=1.0)],
        base_imponible=10.0,
        total_deliverynote=12.1,
    )

    ocr_items = [
        {
            "page_no": 1,
            "text": "A-001",
            "bbox": {"l": 100, "t": 200, "r": 150, "b": 220},
        }
    ]

    mock_annotate.return_value = output_pdf

    result = annotate_document_pdf(
        doc_type="deliverynote",
        input_pdf=pdf_file,
        report=report,
        ocr_items=ocr_items,
        output_pdf=output_pdf,
    )

    assert result == output_pdf
    mock_annotate.assert_called_once()
    # Check that legend_lines_fn was provided
    call_args = mock_annotate.call_args
    assert call_args.kwargs["legend_lines_fn"] is not None


@patch("document_llm_extractor.unified_visualizer.annotate_pdf")
def test_annotate_document_pdf_bank(mock_annotate, tmp_path):
    """Test annotate_document_pdf for bank type."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    output_pdf = tmp_path / "output.pdf"

    report = BankStatement(
        banco="Banco Popular",
        lineas=[],
    )

    ocr_items = [
        {
            "page_no": 1,
            "text": "Banco Popular",
            "bbox": {"l": 100, "t": 200, "r": 200, "b": 220},
        }
    ]

    mock_annotate.return_value = output_pdf

    result = annotate_document_pdf(
        doc_type="bank",
        input_pdf=pdf_file,
        report=report,
        ocr_items=ocr_items,
        output_pdf=output_pdf,
    )

    assert result == output_pdf
    mock_annotate.assert_called_once()
    # Check that legend_lines_fn was provided
    call_args = mock_annotate.call_args
    assert call_args.kwargs["legend_lines_fn"] is not None


@patch("document_llm_extractor.unified_visualizer.annotate_pdf")
def test_annotate_document_pdf_without_redaction(mock_annotate, tmp_path):
    """Test annotate_document_pdf without redaction."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    output_pdf = tmp_path / "output.pdf"

    report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=[ProductoLinea(producto="Caja", cantidad=1.0)],
        base_imponible=10.0,
        total_deliverynote=12.1,
    )

    ocr_items = []

    mock_annotate.return_value = output_pdf

    result = annotate_document_pdf(
        doc_type="deliverynote",
        input_pdf=pdf_file,
        report=report,
        ocr_items=ocr_items,
        output_pdf=output_pdf,
        redact=False,
    )

    assert result == output_pdf
    mock_annotate.assert_called_once()
    # Check that redact is False
    call_args = mock_annotate.call_args
    assert call_args.kwargs["redact"] is False


@patch("document_llm_extractor.unified_visualizer.annotate_pdf")
def test_annotate_document_pdf_with_dpi(mock_annotate, tmp_path):
    """Test annotate_document_pdf with custom DPI."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    output_pdf = tmp_path / "output.pdf"

    report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=[ProductoLinea(producto="Caja", cantidad=1.0)],
        base_imponible=10.0,
        total_deliverynote=12.1,
    )

    ocr_items = []

    mock_annotate.return_value = output_pdf

    result = annotate_document_pdf(
        doc_type="deliverynote",
        input_pdf=pdf_file,
        report=report,
        ocr_items=ocr_items,
        output_pdf=output_pdf,
        dpi=150,
    )

    assert result == output_pdf
    mock_annotate.assert_called_once()
    # Check that dpi was passed
    call_args = mock_annotate.call_args
    assert call_args.kwargs["dpi"] == 150


@patch("document_llm_extractor.unified_visualizer.annotate_pdf")
def test_annotate_document_pdf_all_types(mock_annotate, tmp_path):
    """Test annotate_document_pdf for all document types."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    output_pdf = tmp_path / "output.pdf"

    ocr_items = []

    # Test albaran
    deliverynote_report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=[ProductoLinea(producto="Caja", cantidad=1.0)],
        base_imponible=10.0,
        total_deliverynote=12.1,
    )
    mock_annotate.return_value = output_pdf
    annotate_document_pdf(
        "deliverynote", pdf_file, deliverynote_report, ocr_items, output_pdf
    )

    # Test bank
    bank_report = BankStatement(banco="Test Bank", lineas=[])
    annotate_document_pdf("bank", pdf_file, bank_report, ocr_items, output_pdf)

    # Test payroll
    payroll_report = PayrollReport(devengos=[], deducciones=[])
    annotate_document_pdf("payroll", pdf_file, payroll_report, ocr_items, output_pdf)

    # All should have been called
    assert mock_annotate.call_count == 3
