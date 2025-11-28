"""Layout B: Side-by-side earnings and deductions."""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


def build_layout_b(
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
    """Build Layout B for payroll PDF."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=15,
    )
    story.append(Paragraph(title_txt, title_style))
    story.append(Spacer(1, 0.2 * cm))

    # Compact header
    header_data = [
        [
            Paragraph(f"<b>{empresa_label}</b> {company}", styles["Normal"]),
            Paragraph(f"<b>{periodo_label}</b> {period}", styles["Normal"]),
        ],
        [
            Paragraph(f"<b>{empleado_label}</b> {employee_name}", styles["Normal"]),
            Paragraph(f"<b>DNI:</b> {dni}", styles["Normal"]),
        ],
    ]
    header_table = Table(header_data, colWidths=[7.5 * cm, 7.5 * cm])
    header_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 0.4 * cm))

    # Side-by-side tables
    earnings_data = [
        [devengos_label, ""],
        ["Salario Base", f"{base_salary:.2f} €"],
        ["Paga Extra", f"{extra:.2f} €"],
    ]
    deductions_data = [
        [deducciones_label, ""],
        ["IRPF", f"{irpf:.2f} €"],
        ["Seg. Social", f"{ss_employee:.2f} €"],
    ]

    earnings_table = Table(earnings_data, colWidths=[6 * cm, 4 * cm])
    earnings_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )

    deductions_table = Table(deductions_data, colWidths=[6 * cm, 4 * cm])
    deductions_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightcoral),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )

    side_by_side = Table(
        [[earnings_table, deductions_table]], colWidths=[7.5 * cm, 7.5 * cm]
    )
    side_by_side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(side_by_side)
    story.append(Spacer(1, 0.3 * cm))

    # Summary
    summary_data = [
        [bruto_label, f"{bruto:.2f} €"],
        [deducciones_total_label, f"{total_deducciones:.2f} €"],
        [
            Paragraph(f"<b>{neto_label}:</b>", styles["Normal"]),
            Paragraph(f"<b>{neto:.2f} €</b>", styles["Normal"]),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[10 * cm, 5 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEABOVE", (2, 0), (2, -1), 2, colors.black),
            ]
        )
    )
    story.append(summary_table)
