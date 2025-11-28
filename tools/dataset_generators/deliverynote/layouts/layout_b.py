"""Layout B: Compact layout with minimal info and simplified table."""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


def build_layout_b(
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
    """Build Layout B for delivery note PDF - compact minimal layout.

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
    compact_title = ParagraphStyle(
        "CompactTitle",
        parent=styles["Heading1"],
        fontSize=14,
        alignment=1,  # centered
        textColor=colors.HexColor("#222222"),
        spaceAfter=10,
    )
    story.append(Paragraph(title, compact_title))

    # One-line summary
    summary_txt = (
        f"{supplier} · {numero_label} {deliverynote_num} · "
        f"{fecha_label} {deliverynote_date}"
    )
    story.append(Paragraph(summary_txt, styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    # Simplified 3-column table (no unit price)
    simplified_header = [header[0], header[1], header[3]]  # Product, Quantity, Amount
    simplified_products = []
    for row in products:
        simplified_products.append(
            [row[0], row[1], row[3]]
        )  # Product, Quantity, Amount

    products_data = [simplified_header] + simplified_products
    products_table = Table(products_data, colWidths=[7 * cm, 3 * cm, 5 * cm])
    products_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(products_table)
    story.append(Spacer(1, 0.3 * cm))

    # Compact totals
    totals_data = [
        [base_label, f"{base_total:.2f} €"],
        [f"{iva_label} ({tax_rate}%):", f"{tax_amount:.2f} €"],
        [
            Paragraph(f"<b>{total_label}:</b>", styles["Normal"]),
            Paragraph(f"<b>{total:.2f} €</b>", styles["Normal"]),
        ],
    ]
    totals_table = Table(totals_data, colWidths=[10 * cm, 5 * cm])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEABOVE", (2, 0), (2, -1), 2, colors.black),
            ]
        )
    )
    story.append(totals_table)
