"""Legend generation for delivery note documents."""

from __future__ import annotations

from ...deliverynote.models import DeliveryNoteReport


def make_deliverynote_legend(report: DeliveryNoteReport) -> list[str]:
    """Build legend text lines from a DeliveryNoteReport."""
    lines = [
        f"Delivery Note: {report.numero_deliverynote}",
        f"Fecha: {report.fecha_deliverynote}",
        f"Empresa: {report.nombre_empresa}",
    ]
    if report.nif_cif:
        lines.append(f"NIF/CIF: {report.nif_cif}")
    if report.productos:
        lines.append("")
        lines.append("Productos:")
        for i, p in enumerate(report.productos[:5], 1):
            qty = f"{p.cantidad:g}" if p.cantidad else "?"
            lines.append(f"  {i}. {p.producto} ({qty} {p.unidad or ''})")
    lines.append("")
    lines.append(f"Base: {report.base_imponible:.2f} {report.moneda or 'EUR'}")
    if report.importe_impuestos:
        lines.append(f"IVA: {report.importe_impuestos:.2f}")
    lines.append(f"Total: {report.total_deliverynote:.2f} {report.moneda or 'EUR'}")
    return lines
