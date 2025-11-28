"""Tests for document configuration module.

This module tests:
- DocumentConfig class
- get_config function
- Legend generation functions
- Redaction functions
"""

from __future__ import annotations

import pytest

from document_llm_extractor.bank.models import BankLine, BankStatement
from document_llm_extractor.deliverynote.models import DeliveryNoteReport, ProductoLinea
from document_llm_extractor.document_config import (
    DOCUMENT_CONFIGS,
    DocumentConfig,
    get_config,
)
from document_llm_extractor.payroll.models import Deduccion, Devengo, PayrollReport


def test_get_config_deliverynote():
    """Test get_config for deliverynote document type."""
    config = get_config("deliverynote")
    assert isinstance(config, DocumentConfig)
    assert config.model_class == DeliveryNoteReport
    assert "delivery note" in config.system_prompt.lower()
    assert "{text}" in config.user_prompt_template
    assert config.make_legend_lines is not None
    assert config.redact_lines is not None


def test_get_config_bank():
    """Test get_config for bank document type."""
    config = get_config("bank")
    assert isinstance(config, DocumentConfig)
    assert config.model_class == BankStatement
    assert config.text_limit == 40000
    assert config.make_legend_lines is not None


def test_get_config_payroll():
    """Test get_config for payroll document type."""
    config = get_config("payroll")
    assert isinstance(config, DocumentConfig)
    assert config.model_class == PayrollReport
    assert config.text_limit == 40000
    assert config.make_legend_lines is not None
    assert config.redact_lines is not None


def test_get_config_invalid():
    """Test get_config with invalid document type."""
    with pytest.raises(ValueError, match="Unknown doc_type"):
        get_config("invalid_type")


def test_all_document_types_configured():
    """Test that all expected document types are configured."""
    expected_types = {"deliverynote", "bank", "payroll"}
    assert set(DOCUMENT_CONFIGS.keys()) == expected_types


def test_deliverynote_legend_generation():
    """Test legend generation for DeliveryNoteReport."""
    config = get_config("deliverynote")
    report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        nif_cif="B12345678",
        productos=[
            ProductoLinea(producto="Caja", cantidad=2.0, unidad="ud"),
            ProductoLinea(producto="Bolígrafo", cantidad=10.0, unidad="ud"),
        ],
        base_imponible=100.0,
        importe_impuestos=21.0,
        total_deliverynote=121.0,
        moneda="EUR",
    )
    lines = config.make_legend_lines(report)
    assert "A-001" in "\n".join(lines)
    assert "2025-01-10" in "\n".join(lines)
    assert "ACME SA" in "\n".join(lines)
    assert "B12345678" in "\n".join(lines)
    assert "Caja" in "\n".join(lines)
    assert "100.00" in "\n".join(lines)
    assert "121.00" in "\n".join(lines)


def test_deliverynote_legend_without_nif():
    """Test deliverynote legend generation without NIF."""
    config = get_config("deliverynote")
    report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=[ProductoLinea(producto="Caja", cantidad=1.0)],
        base_imponible=10.0,
        total_deliverynote=12.1,
    )
    lines = config.make_legend_lines(report)
    text = "\n".join(lines)
    assert "NIF/CIF" not in text or "None" not in text


def test_bank_legend_generation():
    """Test legend generation for BankStatement."""
    config = get_config("bank")
    statement = BankStatement(
        banco="Banco Popular",
        titular="Juan Pérez",
        iban="ES91 2100 0418 4502 0005 1332",
        periodo_desde="2025-01-01",
        periodo_hasta="2025-01-31",
        moneda="EUR",
        lineas=[
            BankLine(fecha="2025-01-05", concepto="Transferencia", importe=1000.0),
            BankLine(fecha="2025-01-10", concepto="Pago", importe=-50.0),
        ],
        saldo_inicial=4000.0,
        saldo_final=4950.0,
    )
    lines = config.make_legend_lines(statement)
    text = "\n".join(lines)
    assert "Banco Popular" in text
    assert "Juan Pérez" in text
    assert "2025-01-01" in text
    assert "2025-01-31" in text
    assert "4000.00" in text
    assert "4950.00" in text


def test_payroll_legend_generation():
    """Test legend generation for PayrollReport."""
    config = get_config("payroll")
    report = PayrollReport(
        empresa_nif="B12345678",
        empleado_dni="12345678A",
        periodo="2025-01",
        categoria="Ingeniero",
        iban="ES91 2100 0418 4502 0005 1332",
        devengos=[
            Devengo(concepto="Salario base", importe=2000.0),
            Devengo(concepto="Plus transporte", importe=50.0),
        ],
        deducciones=[
            Deduccion(concepto="IRPF", importe=300.0),
            Deduccion(concepto="Seguridad Social", importe=200.0),
        ],
        bruto=2050.0,
        total_deducciones=500.0,
        neto=1550.0,
    )
    lines = config.make_legend_lines(report)
    text = "\n".join(lines)
    assert "B12345678" in text
    assert "12345678A" in text
    assert "2025-01" in text
    assert "Salario base" in text
    assert "IRPF" in text
    assert "2050.00" in text
    assert "1550.00" in text


def test_legend_truncation():
    """Test that legends truncate long lists."""
    config = get_config("deliverynote")
    # Create report with more than 5 products
    productos = [
        ProductoLinea(producto=f"Producto {i}", cantidad=1.0) for i in range(10)
    ]
    report = DeliveryNoteReport(
        numero_deliverynote="A-001",
        fecha_deliverynote="2025-01-10",
        nombre_empresa="ACME SA",
        productos=productos,
        base_imponible=100.0,
        total_deliverynote=121.0,
    )
    lines = config.make_legend_lines(report)
    # Should only show first 5 products (indices 0-4)
    text = "\n".join(lines)
    assert "Producto 0" in text
    assert "Producto 4" in text
    # Product 5 should not appear (or appear less frequently)
    product_5_count = text.count("Producto 5")
    assert product_5_count == 0  # Should not appear in legend


def test_redaction_payroll():
    """Test redaction function for payroll documents."""
    config = get_config("payroll")
    lines = [
        "Empleado DNI: 12345678A",
        "Empresa NIF: B12345678",
        "Neto: 1550.00 EUR",
    ]
    redacted = config.redact_lines(lines)
    redacted_text = "\n".join(redacted)
    # Should redact DNI/NIE
    assert "12345678A" not in redacted_text or "REDACTED" in redacted_text


def test_default_redaction():
    """Test default redaction function."""
    config = get_config("deliverynote")
    lines = [
        "Delivery Note: A-001",
        "Email: test@example.com",
        "Phone: +34 600 123 456",
    ]
    redacted = config.redact_lines(lines)
    redacted_text = "\n".join(redacted)
    # Should redact email and phone
    assert "test@example.com" not in redacted_text or "REDACTED" in redacted_text
    assert "+34 600 123 456" not in redacted_text or "REDACTED" in redacted_text


def test_text_limit_configuration():
    """Test that text_limit is properly configured."""
    config_deliverynote = get_config("deliverynote")
    config_bank = get_config("bank")

    # Delivery note should not have text limit (None)
    assert config_deliverynote.text_limit is None

    # Bank should have text limit
    assert config_bank.text_limit == 40000
    assert config_bank.text_limit is not None
