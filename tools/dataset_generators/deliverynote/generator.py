"""Delivery note PDF generator with multiple layout templates."""

from __future__ import annotations

import json
import random
import sys
from datetime import date
from pathlib import Path

from pdf2image import convert_from_path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
from document_llm_extractor.deliverynote.models import DeliveryNoteReport, ProductoLinea

from .constants import (
    CATALAN_COMPANIES,
    ENGLISH_COMPANIES,
    LANGS,
    QUALITIES,
    SAMPLES_PER_LANG,
    SPANISH_COMPANIES,
)
from .layouts.layout_a import build_layout_a
from .layouts.layout_b import build_layout_b
from .layouts.layout_c import build_layout_c

ROOT = Path("data") / "deliverynote"
PDF_ROOT = ROOT / "pdf"
IMAGES_ROOT = ROOT / "images"
GROUND_TRUTH_ROOT = ROOT / "ground_truth"


def generate_deliverynote_pdf(language: str, output_path: Path) -> DeliveryNoteReport:
    """Generate one synthetic delivery note PDF with random layout selection.

    We randomize between three different layout structures so the resulting
    documents are visually and structurally diverse:

      - layout A: classic layout (header + full info table + 4-col products table)
      - layout B: compact layout (minimal info + 3-col products table)
      - layout C: summary-first layout (summary box + 4-col products table)
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    story: list = []

    if language == "es":
        supplier = random.choice(SPANISH_COMPANIES)
        city_choices = ["Madrid", "Barcelona", "Valencia", "Sevilla"]
        title = "ALBARÁN"
        base_label = "Base Imponible:"
        iva_label = "IVA"
        total_label = "Total Albarán:"
        numero_label = "Número Albarán:"
        fecha_label = "Fecha:"
        empresa_label = "Empresa:"
        direccion_label = "Dirección:"
        codigo_postal_label = "Código Postal:"
        poblacion_label = "Población:"
    elif language == "ca":
        supplier = random.choice(CATALAN_COMPANIES)
        city_choices = ["Barcelona", "Girona", "Lleida", "Tarragona"]
        title = "ALBARÀ"
        base_label = "Base imposable:"
        iva_label = "IVA"
        total_label = "Total albarà:"
        numero_label = "Número d'albarà:"
        fecha_label = "Data:"
        empresa_label = "Empresa:"
        direccion_label = "Adreça:"
        codigo_postal_label = "Codi postal:"
        poblacion_label = "Població:"
    else:  # en
        supplier = random.choice(ENGLISH_COMPANIES)
        city_choices = ["Madrid", "Barcelona", "London", "Valencia"]
        title = "DELIVERY NOTE"
        base_label = "Subtotal:"
        iva_label = "VAT"
        total_label = "Total:"
        numero_label = "Delivery Note No.:"
        fecha_label = "Date:"
        empresa_label = "Company:"
        direccion_label = "Address:"
        codigo_postal_label = "Postal Code:"
        poblacion_label = "City:"

    nif = f"{random.randint(10000000, 99999999)}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"
    address = (
        f"Calle {random.choice(['Mayor', 'Real', 'Nueva'])} {random.randint(1, 100)}"
    )
    postal = f"{random.randint(28000, 28999)}"
    city = random.choice(city_choices)

    deliverynote_num = f"DN-{random.randint(10000, 99999)}"
    deliverynote_date = date.today().strftime("%Y-%m-%d")

    products = []
    productos_list = []
    base_total = 0.0
    for _ in range(random.randint(3, 8)):
        product = random.choice(
            ["Producto A", "Servicio B", "Material C", "Componente D"]
        )
        qty = random.randint(1, 10)
        price = round(random.uniform(10, 500), 2)
        total = round(qty * price, 2)
        base_total += total
        products.append([product, f"{qty}", f"{price:.2f} €", f"{total:.2f} €"])
        productos_list.append(
            ProductoLinea(
                producto=product,
                cantidad=float(qty),
                precio_unitario=price,
                importe_linea=total,
            )
        )

    tax_rate = 21.0
    tax_amount = round(base_total * 0.21, 2)
    total = round(base_total + tax_amount, 2)

    header = (
        ["Producto", "Cantidad", "Precio Unit.", "Importe"]
        if language == "es"
        else (
            ["Producte", "Quantitat", "Preu unit.", "Import"]
            if language == "ca"
            else ["Product", "Quantity", "Unit price", "Amount"]
        )
    )

    # Randomly select layout
    layout = random.choice(["A", "B", "C"])

    # Build layout
    if layout == "A":
        build_layout_a(
            story,
            title,
            numero_label,
            fecha_label,
            empresa_label,
            direccion_label,
            codigo_postal_label,
            poblacion_label,
            base_label,
            iva_label,
            total_label,
            deliverynote_num,
            deliverynote_date,
            supplier,
            nif,
            address,
            postal,
            city,
            header,
            products,
            base_total,
            tax_rate,
            tax_amount,
            total,
        )
    elif layout == "B":
        build_layout_b(
            story,
            title,
            numero_label,
            fecha_label,
            empresa_label,
            direccion_label,
            codigo_postal_label,
            poblacion_label,
            base_label,
            iva_label,
            total_label,
            deliverynote_num,
            deliverynote_date,
            supplier,
            nif,
            address,
            postal,
            city,
            header,
            products,
            base_total,
            tax_rate,
            tax_amount,
            total,
        )
    else:  # layout == "C"
        build_layout_c(
            story,
            title,
            numero_label,
            fecha_label,
            empresa_label,
            direccion_label,
            codigo_postal_label,
            poblacion_label,
            base_label,
            iva_label,
            total_label,
            deliverynote_num,
            deliverynote_date,
            supplier,
            nif,
            address,
            postal,
            city,
            header,
            products,
            base_total,
            tax_rate,
            tax_amount,
            total,
        )

    doc.build(story)

    return DeliveryNoteReport(
        numero_deliverynote=deliverynote_num,
        fecha_deliverynote=deliverynote_date,
        nombre_empresa=supplier,
        nif_cif=nif,
        direccion=address,
        codigo_postal=postal,
        poblacion=city,
        productos=productos_list,
        base_imponible=base_total,
        porcentaje_impuestos=tax_rate,
        importe_impuestos=tax_amount,
        importe_con_impuestos=total,
        total_deliverynote=total,
        moneda="EUR",
    )


def pdf_to_jpgs(pdf_path: Path, images_dir: Path) -> None:
    """Convert one PDF to JPGs at multiple qualities."""
    images_dir.mkdir(parents=True, exist_ok=True)
    try:
        pages = convert_from_path(str(pdf_path))
    except Exception as exc:
        rel = pdf_path.relative_to(ROOT.parent)
        print(f"[error] Failed to convert {rel}: {exc}")
        return

    rel = pdf_path.relative_to(ROOT.parent)
    for page_idx, page in enumerate(pages, start=1):
        for q in QUALITIES:
            out_name = f"{pdf_path.stem}_p{page_idx}_q{q}.jpg"
            out_path = images_dir / out_name
            if out_path.exists():
                continue
            page.save(out_path, "JPEG", quality=q, optimize=True)
            print(f"[img] {rel} -> {out_path.relative_to(ROOT.parent)}")


def main() -> None:
    """Main entry point for delivery note dataset generation."""
    print("=" * 70)
    print("Synthetic Delivery Note Dataset Generator (PDF + JPG)")
    print("=" * 70)

    for lang in LANGS:
        pdf_dir = PDF_ROOT / lang
        img_dir = IMAGES_ROOT / lang
        pdf_dir.mkdir(parents=True, exist_ok=True)
        img_dir.mkdir(parents=True, exist_ok=True)

        ground_truth_dir = GROUND_TRUTH_ROOT / lang
        ground_truth_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n[lang={lang}] generating {SAMPLES_PER_LANG} PDFs and JPGs...")
        for i in range(1, SAMPLES_PER_LANG + 1):
            pdf_path = pdf_dir / f"deliverynote_{lang}_{i:02d}.pdf"
            ground_truth = generate_deliverynote_pdf(lang, pdf_path)
            print(f"[pdf] {pdf_path.relative_to(ROOT.parent)}")

            gt_path = (
                ground_truth_dir / f"deliverynote_{lang}_{i:02d}_ground_truth.json"
            )
            gt_path.write_text(
                json.dumps(ground_truth.model_dump(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            pdf_to_jpgs(pdf_path, img_dir)

    print("\nDone.")
    print(f"PDFs   in: {PDF_ROOT}")
    print(f"Images in: {IMAGES_ROOT}")


if __name__ == "__main__":
    main()
