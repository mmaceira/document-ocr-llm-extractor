"""Payroll PDF generator."""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
from document_llm_extractor.payroll.models import Deduccion, Devengo, PayrollReport

from .constants import (
    CATALAN_COMPANIES,
    CATALAN_NAMES,
    CATALAN_SURNAMES,
    ENGLISH_COMPANIES,
    ENGLISH_NAMES,
    ENGLISH_SURNAMES,
    SPANISH_COMPANIES,
    SPANISH_NAMES,
    SPANISH_SURNAMES,
)
from .layouts.layout_a import build_layout_a
from .layouts.layout_b import build_layout_b
from .layouts.layout_c import build_layout_c


def generate_dni_number() -> str:
    """Generate a pseudo-valid Spanish DNI number."""
    letters = "TRWAGMYFPDXBNJZSQVHLCKE"
    number = random.randint(10000000, 99999999)
    letter = letters[number % 23]
    return f"{number}{letter}"


def generate_payroll_pdf(language: str, output_path: Path) -> PayrollReport:
    """Generate one synthetic payroll PDF with 3 different structure variants.

    Args:
        language: Language code (es, en, ca).
        output_path: Path to save the PDF.

    Returns:
        PayrollReport: Ground truth data for the generated document.
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    story: list = []

    layout = random.choice(["A", "B", "C"])

    if language == "es":
        company = random.choice(SPANISH_COMPANIES)
        title_txt = "NÓMINA"
        empresa_label = "Empresa:"
        empleado_label = "Empleado:"
        periodo_label = "Período:"
        devengos_label = "DEVENGOS"
        deducciones_label = "DEDUCCIONES"
        bruto_label = "Total Bruto:"
        deducciones_total_label = "Total Deducciones:"
        neto_label = "Líquido a Percibir:"
        employee_name = (
            f"{random.choice(SPANISH_NAMES)} {random.choice(SPANISH_SURNAMES)}"
        )
    elif language == "en":
        company = random.choice(ENGLISH_COMPANIES)
        title_txt = "PAYSLIP"
        empresa_label = "Company:"
        empleado_label = "Employee:"
        periodo_label = "Period:"
        devengos_label = "EARNINGS"
        deducciones_label = "DEDUCTIONS"
        bruto_label = "Gross Total:"
        deducciones_total_label = "Total Deductions:"
        neto_label = "Net Pay:"
        employee_name = (
            f"{random.choice(ENGLISH_NAMES)} {random.choice(ENGLISH_SURNAMES)}"
        )
    else:  # ca
        company = random.choice(CATALAN_COMPANIES)
        title_txt = "NÒMINA"
        empresa_label = "Empresa:"
        empleado_label = "Empleat:"
        periodo_label = "Període:"
        devengos_label = "DEVENGS"
        deducciones_label = "DEDUCCIONS"
        bruto_label = "Total brut:"
        deducciones_total_label = "Total deduccions:"
        neto_label = "Líquid a percebre:"
        employee_name = (
            f"{random.choice(CATALAN_NAMES)} {random.choice(CATALAN_SURNAMES)}"
        )

    nif = f"{random.randint(10000000, 99999999)}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"
    dni = generate_dni_number()
    period = (date.today() - timedelta(days=30)).strftime("%Y-%m")

    base_salary = round(random.uniform(1500, 4000), 2)
    extra = round(base_salary * 0.1, 2)
    bruto = base_salary + extra

    irpf = round(bruto * random.uniform(0.10, 0.20), 2)
    ss_employee = round(bruto * 0.06, 2)
    total_deducciones = irpf + ss_employee
    neto = round(bruto - total_deducciones, 2)

    # Create ground truth structures
    devengos_list = [
        Devengo(concepto="Salario Base", importe=base_salary),
        Devengo(concepto="Paga Extra", importe=extra),
    ]
    deducciones_list = [
        Deduccion(concepto="IRPF", importe=irpf),
        Deduccion(concepto="Seguridad Social", importe=ss_employee),
    ]

    # Build layout
    if layout == "A":
        build_layout_a(
            story,
            title_txt,
            empresa_label,
            empleado_label,
            periodo_label,
            devengos_label,
            deducciones_label,
            bruto_label,
            deducciones_total_label,
            neto_label,
            company,
            nif,
            employee_name,
            dni,
            period,
            base_salary,
            extra,
            irpf,
            ss_employee,
            bruto,
            total_deducciones,
            neto,
        )
    elif layout == "B":
        build_layout_b(
            story,
            title_txt,
            empresa_label,
            empleado_label,
            periodo_label,
            devengos_label,
            deducciones_label,
            bruto_label,
            deducciones_total_label,
            neto_label,
            company,
            employee_name,
            dni,
            period,
            base_salary,
            extra,
            irpf,
            ss_employee,
            bruto,
            total_deducciones,
            neto,
        )
    else:  # layout == "C"
        build_layout_c(
            story,
            title_txt,
            empresa_label,
            empleado_label,
            periodo_label,
            bruto_label,
            deducciones_total_label,
            neto_label,
            company,
            employee_name,
            period,
            base_salary,
            extra,
            irpf,
            ss_employee,
            bruto,
            total_deducciones,
            neto,
        )

    doc.build(story)

    # Create and return ground truth
    return PayrollReport(
        empresa_nif=nif,
        empleado_dni=dni,
        periodo=period,
        devengos=devengos_list,
        deducciones=deducciones_list,
        bruto=bruto,
        total_deducciones=total_deducciones,
        neto=neto,
    )
