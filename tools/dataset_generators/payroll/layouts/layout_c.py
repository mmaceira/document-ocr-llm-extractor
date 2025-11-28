"""Layout C: Summary-first with detailed breakdown below."""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


def build_layout_c(
    story: list,
    title_txt: str,
    empresa_label: str,
    empleado_label: str,
    periodo_label: str,
    bruto_label: str,
    deducciones_total_label: str,
    neto_label: str,
    company: str,
    employee_name: str,
    period: str,
    base_salary: float,
    extra: float,
    irpf: float,
    ss_employee: float,
    bruto: float,
    total_deducciones: float,
    neto: float,
) -> None:
    """Build Layout C for payroll PDF."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#34495e"),
        spaceAfter=10,
    )
    story.append(Paragraph(title_txt, title_style))
    story.append(Spacer(1, 0.2 * cm))

    # Summary box at top
    summary_box = [
        [
            Paragraph(f"<b>{neto_label}</b>", styles["Normal"]),
            Paragraph(f"<b>{neto:.2f} €</b>", styles["Normal"]),
        ],
        [bruto_label, f"{bruto:.2f} €"],
        [deducciones_total_label, f"{total_deducciones:.2f} €"],
    ]
    summary_table = Table(summary_box, colWidths=[10 * cm, 5 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 14),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.4 * cm))

    # Compact info
    info_text = (
        f"<b>{empresa_label}</b> {company} | "
        f"<b>{empleado_label}</b> {employee_name} | "
        f"<b>{periodo_label}</b> {period}"
    )
    story.append(Paragraph(info_text, styles["Normal"]))
    story.append(Spacer(1, 0.3 * cm))

    # Combined breakdown
    breakdown_data = [
        ["Concepto", "Tipo", "Importe"],
        ["Salario Base", "Devengo", f"{base_salary:.2f} €"],
        ["Paga Extra", "Devengo", f"{extra:.2f} €"],
        ["IRPF", "Deducción", f"-{irpf:.2f} €"],
        ["Seg. Social", "Deducción", f"-{ss_employee:.2f} €"],
    ]
    breakdown_table = Table(breakdown_data, colWidths=[7 * cm, 4 * cm, 4 * cm])
    breakdown_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(breakdown_table)
