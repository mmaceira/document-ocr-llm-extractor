"""Comprehensive tests for all document models.

This module tests Pydantic models for all document types:
- AlbaranReport and ProductoLinea
- BankStatement and BankLine
- PayrollReport, Devengo, and Deduccion
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from document_llm_extractor.bank.models import BankLine, BankStatement
from document_llm_extractor.deliverynote.models import DeliveryNoteReport, ProductoLinea
from document_llm_extractor.payroll.models import Deduccion, Devengo, PayrollReport

# ============================================================================
# DeliveryNoteReport Tests
# ============================================================================


def test_albaran_report_minimal():
    """Test DeliveryNoteReport with minimal required fields."""
    data = {
        "numero_deliverynote": "A-001",
        "fecha_deliverynote": "2025-01-10",
        "nombre_empresa": "ACME SA",
        "productos": [{"producto": "Caja", "cantidad": 1.0}],
        "base_imponible": 10.0,
        "total_deliverynote": 12.1,
    }
    report = DeliveryNoteReport.model_validate(data)
    assert report.numero_deliverynote == "A-001"
    assert report.fecha_deliverynote == "2025-01-10"
    assert report.nombre_empresa == "ACME SA"
    assert len(report.productos) == 1
    assert report.base_imponible == 10.0
    assert report.total_deliverynote == 12.1
    assert report.moneda == "EUR"  # Default value


def test_albaran_report_full():
    """Test DeliveryNoteReport with all fields."""
    data = {
        "numero_deliverynote": "A-001",
        "fecha_deliverynote": "2025-01-10",
        "categoria_gasto": "Oficina",
        "fecha_registro": "2025-01-11",
        "moneda": "USD",
        "estado": "Pagado",
        "fichero_datalake": "s3://bucket/file.pdf",
        "nombre_empresa": "ACME SA",
        "nif_cif": "B12345678",
        "direccion": "Calle Principal 1",
        "codigo_postal": "28001",
        "poblacion": "Madrid",
        "productos": [
            {
                "producto": "Caja",
                "descripcion": "Caja de cartón",
                "cantidad": 2.0,
                "unidad": "ud",
                "precio_unitario": 5.0,
                "importe_linea": 10.0,
            }
        ],
        "base_imponible": 10.0,
        "porcentaje_impuestos": 21.0,
        "importe_impuestos": 2.1,
        "importe_con_impuestos": 12.1,
        "porcentaje_retencion": 15.0,
        "importe_retencion": 1.5,
        "total_deliverynote": 12.1,
    }
    report = DeliveryNoteReport.model_validate(data)
    assert report.numero_deliverynote == "A-001"
    assert report.categoria_gasto == "Oficina"
    assert report.nif_cif == "B12345678"
    assert len(report.productos) == 1
    assert report.productos[0].producto == "Caja"
    assert report.productos[0].cantidad == 2.0
    assert report.porcentaje_impuestos == 21.0


def test_albaran_report_missing_required():
    """Test DeliveryNoteReport validation with missing required fields."""
    with pytest.raises(ValidationError) as exc_info:
        DeliveryNoteReport.model_validate({})
    errors = exc_info.value.errors()
    required_fields = {
        "numero_deliverynote",
        "fecha_deliverynote",
        "nombre_empresa",
        "productos",
        "base_imponible",
        "total_deliverynote",
    }
    error_fields = {err["loc"][0] for err in errors if err["type"] == "missing"}
    assert required_fields.issubset(error_fields)


def test_albaran_report_extra_fields():
    """Test DeliveryNoteReport rejects extra fields."""
    data = {
        "numero_deliverynote": "A-001",
        "fecha_deliverynote": "2025-01-10",
        "nombre_empresa": "ACME SA",
        "productos": [{"producto": "Caja", "cantidad": 1.0}],
        "base_imponible": 10.0,
        "total_deliverynote": 12.1,
        "extra_field": "should fail",
    }
    with pytest.raises(ValidationError) as exc_info:
        DeliveryNoteReport.model_validate(data)
    assert any("extra_field" in str(err) for err in exc_info.value.errors())


def test_producto_linea():
    """Test ProductoLinea model."""
    data = {
        "producto": "Producto A",
        "cantidad": 5.0,
        "unidad": "kg",
        "precio_unitario": 10.5,
        "importe_linea": 52.5,
    }
    producto = ProductoLinea.model_validate(data)
    assert producto.producto == "Producto A"
    assert producto.cantidad == 5.0
    assert producto.unidad == "kg"
    assert producto.precio_unitario == 10.5
    assert producto.importe_linea == 52.5


def test_producto_linea_minimal():
    """Test ProductoLinea with minimal required fields."""
    data = {
        "producto": "Producto A",
        "cantidad": 1.0,
    }
    producto = ProductoLinea.model_validate(data)
    assert producto.producto == "Producto A"
    assert producto.cantidad == 1.0
    assert producto.descripcion is None
    assert producto.unidad is None


# ============================================================================
# BankStatement Tests
# ============================================================================


def test_bank_statement_minimal():
    """Test BankStatement with minimal fields."""
    data = {
        "lineas": [],
    }
    statement = BankStatement.model_validate(data)
    assert statement.lineas == []
    assert statement.moneda == "EUR"  # Default value
    assert statement.banco is None


def test_bank_statement_full():
    """Test BankStatement with all fields."""
    data = {
        "banco": "Banco Popular",
        "titular": "Juan Pérez",
        "iban": "ES91 2100 0418 4502 0005 1332",
        "periodo_desde": "2025-01-01",
        "periodo_hasta": "2025-01-31",
        "moneda": "EUR",
        "lineas": [
            {
                "fecha": "2025-01-05",
                "concepto": "Transferencia recibida",
                "importe": 1000.0,
                "saldo": 5000.0,
            },
            {
                "fecha": "2025-01-10",
                "concepto": "Pago factura",
                "importe": -50.0,
                "saldo": 4950.0,
            },
        ],
        "saldo_inicial": 4000.0,
        "saldo_final": 4950.0,
    }
    statement = BankStatement.model_validate(data)
    assert statement.banco == "Banco Popular"
    assert statement.titular == "Juan Pérez"
    assert len(statement.lineas) == 2
    assert statement.lineas[0].importe == 1000.0
    assert statement.lineas[1].importe == -50.0
    assert statement.saldo_inicial == 4000.0
    assert statement.saldo_final == 4950.0


def test_bank_line():
    """Test BankLine model."""
    data = {
        "fecha": "2025-01-15",
        "concepto": "Compra en tienda",
        "importe": -25.50,
    }
    line = BankLine.model_validate(data)
    assert line.fecha == "2025-01-15"
    assert line.concepto == "Compra en tienda"
    assert line.importe == -25.50
    assert line.saldo is None


def test_bank_line_with_saldo():
    """Test BankLine with saldo field."""
    data = {
        "fecha": "2025-01-15",
        "concepto": "Depósito",
        "importe": 500.0,
        "saldo": 5500.0,
    }
    line = BankLine.model_validate(data)
    assert line.saldo == 5500.0


# ============================================================================
# PayrollReport Tests
# ============================================================================


def test_payroll_report_minimal():
    """Test PayrollReport with minimal fields."""
    data = {
        "devengos": [],
        "deducciones": [],
    }
    report = PayrollReport.model_validate(data)
    assert report.devengos == []
    assert report.deducciones == []
    assert report.empresa_nif is None


def test_payroll_report_full():
    """Test PayrollReport with all fields."""
    data = {
        "empresa_nif": "B12345678",
        "empleado_dni": "12345678A",
        "periodo": "2025-01",
        "categoria": "Ingeniero",
        "iban": "ES91 2100 0418 4502 0005 1332",
        "devengos": [
            {"concepto": "Salario base", "importe": 2000.0},
            {"concepto": "Plus transporte", "importe": 50.0},
        ],
        "deducciones": [
            {"concepto": "IRPF", "importe": 300.0},
            {"concepto": "Seguridad Social", "importe": 200.0},
        ],
        "bruto": 2050.0,
        "total_deducciones": 500.0,
        "neto": 1550.0,
    }
    report = PayrollReport.model_validate(data)
    assert report.empresa_nif == "B12345678"
    assert report.empleado_dni == "12345678A"
    assert report.periodo == "2025-01"
    assert len(report.devengos) == 2
    assert len(report.deducciones) == 2
    assert report.bruto == 2050.0
    assert report.neto == 1550.0


def test_devengo():
    """Test Devengo model."""
    data = {
        "concepto": "Salario base",
        "importe": 2000.0,
    }
    devengo = Devengo.model_validate(data)
    assert devengo.concepto == "Salario base"
    assert devengo.importe == 2000.0


def test_deduccion():
    """Test Deduccion model."""
    data = {
        "concepto": "IRPF",
        "importe": 300.0,
    }
    deduccion = Deduccion.model_validate(data)
    assert deduccion.concepto == "IRPF"
    assert deduccion.importe == 300.0
