"""Layout A: Classic vertical layout with separate sections."""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


def build_layout_a(
    story: list,
    title_txt: str,
    empresa_label: str,
    empleado_label: str,
    periodo_label: str,
    devengos_label: str,
    deducciones_label: str,
    bruto_label: str,
    deducciones_total_label: str,
    neto_label: str,
    company: str,
    nif: str,
    employee_name: str,
    dni: str,
    period: str,
    base_salary: float,
    extra: float,
    irpf: float,
    ss_employee: float,
    bruto: float,
    total_deducciones: float,
    neto: float,
) -> None:
    """Build Layout A for payroll PDF.

    Args:
        story: ReportLab story list to append elements to.
        title_txt: Title text.
        empresa_label: Company label.
        empleado_label: Employee label.
        periodo_label: Period label.
        devengos_label: Earnings label.
        deducciones_label: Deductions label.
        bruto_label: Gross total label.
        deducciones_total_label: Total deductions label.
        neto_label: Net pay label.
        company: Company name.
        nif: Company NIF.
        employee_name: Employee name.
        dni: Employee DNI.
        period: Period string.
        base_salary: Base salary amount.
        extra: Extra pay amount.
        irpf: IRPF deduction amount.
        ss_employee: Social security deduction amount.
        bruto: Gross total.
        total_deducciones: Total deductions.
        neto: Net pay.
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=20,
    )
    story.append(Paragraph(title_txt, title_style))
    story.append(Spacer(1, 0.3 * cm))

    info_data = [
        [empresa_label, company],
        ["NIF:", nif],
        [empleado_label, employee_name],
        ["DNI:", dni],
        [periodo_label, period],
    ]

    info_table = Table(info_data, colWidths=[4 * cm, 11 * cm])
    info_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 0.5 * cm))

    earnings_data = [["Concepto", "Importe"]]
    earnings_data.append(["Salario Base", f"{base_salary:.2f} €"])
    earnings_data.append(["Paga Extra", f"{extra:.2f} €"])

    earnings_table = Table(earnings_data, colWidths=[10 * cm, 5 * cm])
    earnings_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(Paragraph(f"<b>{devengos_label}</b>", styles["Normal"]))
    story.append(earnings_table)
    story.append(Spacer(1, 0.3 * cm))

    deductions_data = [["Concepto", "Importe"]]
    deductions_data.append(["IRPF", f"{irpf:.2f} €"])
    deductions_data.append(["Seguridad Social", f"{ss_employee:.2f} €"])

    deductions_table = Table(deductions_data, colWidths=[10 * cm, 5 * cm])
    deductions_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(Paragraph(f"<b>{deducciones_label}</b>", styles["Normal"]))
    story.append(deductions_table)
    story.append(Spacer(1, 0.3 * cm))

    totals_data = [
        [bruto_label, f"{bruto:.2f} €"],
        [deducciones_total_label, f"{total_deducciones:.2f} €"],
        [
            Paragraph(f"<b>{neto_label}:</b>", styles["Normal"]),
            Paragraph(f"<b>{neto:.2f} €</b>", styles["Normal"]),
        ],
    ]

    totals_table = Table(totals_data, colWidths=[10 * cm, 5 * cm])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(totals_table)
