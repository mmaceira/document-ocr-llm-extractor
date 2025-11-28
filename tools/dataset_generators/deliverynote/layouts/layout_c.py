"""Layout C: Summary-first layout with info box and detailed table."""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


def build_layout_c(
    story: list,
    title: str,
    numero_label: str,
    fecha_label: str,
    empresa_label: str,
    direccion_label: str,
    codigo_postal_label: str,
    poblacion_label: str,
    base_label: str,
    iva_label: str,
    total_label: str,
    deliverynote_num: str,
    deliverynote_date: str,
    supplier: str,
    nif: str,
    address: str,
    postal: str,
    city: str,
    header: list[str],
    products: list[list[str]],
    base_total: float,
    tax_rate: float,
    tax_amount: float,
    total: float,
) -> None:
    """Build Layout C for delivery note PDF - summary-first layout.

    Args:
        story: ReportLab story list to append elements to.
        title: Title text (ALBARÁN, ALBARÀ, DELIVERY NOTE).
        numero_label: Delivery note number label.
        fecha_label: Date label.
        empresa_label: Company label.
        direccion_label: Address label.
        codigo_postal_label: Postal code label.
        poblacion_label: City label.
        base_label: Base amount label.
        iva_label: Tax label.
        total_label: Total label.
        deliverynote_num: Delivery note number.
        deliverynote_date: Delivery note date.
        supplier: Supplier/company name.
        nif: Company NIF/CIF.
        address: Company address.
        postal: Postal code.
        city: City name.
        header: Product table header row.
        products: List of product rows.
        base_total: Base total amount.
        tax_rate: Tax rate percentage.
        tax_amount: Tax amount.
        total: Total amount.
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=15,
    )
    story.append(Paragraph(f"{supplier}", title_style))
    story.append(Paragraph(title, styles["Heading3"]))
    story.append(Spacer(1, 0.2 * cm))

    # Summary box first
    summary_data = [
        [numero_label, deliverynote_num],
        [fecha_label, deliverynote_date],
        [empresa_label, supplier],
        ["NIF/CIF:", nif],
        [direccion_label, address],
        [codigo_postal_label, postal],
        [poblacion_label, city],
        [base_label, f"{base_total:.2f} EUR"],
        [f"{iva_label} ({tax_rate}%):", f"{tax_amount:.2f} EUR"],
        [total_label, f"{total:.2f} EUR"],
    ]

    summary_table = Table(summary_data, colWidths=[4 * cm, 11 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("LINEABOVE", (6, 0), (6, -1), 1, colors.black),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.5 * cm))

    # Detailed products table
    products_data = [header] + products
    products_table = Table(products_data, colWidths=[6 * cm, 2 * cm, 3 * cm, 4 * cm])
    products_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (2, 0), (3, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(products_table)
