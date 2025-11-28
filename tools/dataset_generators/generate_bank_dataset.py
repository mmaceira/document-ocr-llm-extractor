#!/usr/bin/env python3
"""Generate synthetic bank PDFs and corresponding JPGs in a single run.

Layout:
  data/
    bank/
      pdf/{es,en,ca}/*.pdf
      images/{es,en,ca}/*_p<page>_q<quality>.jpg

Qualities used (good → bad): 90, 40, 10.
"""

from __future__ import annotations

import json
import random
import string
import sys
from datetime import date, timedelta
from pathlib import Path

from pdf2image import convert_from_path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from document_llm_extractor.bank.models import BankLine, BankStatement

ROOT = Path("data") / "bank"
PDF_ROOT = ROOT / "pdf"
IMAGES_ROOT = ROOT / "images"
GROUND_TRUTH_ROOT = ROOT / "ground_truth"

LANGS = ("es", "en", "ca")
SAMPLES_PER_LANG = 5
QUALITIES = (90, 40, 10)


# --- Synthetic bank statement generation helpers -----------------------------

SPANISH_NAMES = [
    "María",
    "José",
    "Carmen",
    "Juan",
    "Ana",
    "Francisco",
    "Laura",
    "Antonio",
    "Isabel",
    "Manuel",
    "Lucía",
    "Pedro",
    "Elena",
    "Carlos",
    "Sofía",
    "Miguel",
]

ENGLISH_NAMES = [
    "John",
    "Mary",
    "James",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "William",
    "Elizabeth",
    "David",
    "Barbara",
    "Richard",
    "Susan",
    "Joseph",
    "Jessica",
]

CATALAN_NAMES = [
    "Jordi",
    "Montserrat",
    "Núria",
    "Oriol",
    "Laia",
    "Pere",
    "Mercè",
    "Carles",
]

SPANISH_SURNAMES = [
    "García",
    "Rodríguez",
    "González",
    "Fernández",
    "López",
    "Martínez",
    "Sánchez",
    "Pérez",
    "Gómez",
    "Martín",
    "Jiménez",
    "Ruiz",
    "Hernández",
    "Díaz",
    "Moreno",
    "Álvarez",
]

ENGLISH_SURNAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
]

CATALAN_SURNAMES = [
    "Puig",
    "Ferrer",
    "Serra",
    "Vila",
    "Pons",
    "Ribas",
    "Solé",
    "Roca",
]

SPANISH_BANKS = ["BBVA", "Santander", "CaixaBank", "Bankia", "Sabadell", "Unicaja"]
ENGLISH_BANKS = [
    "Chase",
    "Bank of America",
    "Wells Fargo",
    "Citibank",
    "HSBC",
    "Barclays",
]


def generate_iban(country: str = "ES") -> str:
    """Generate a simple pseudo-IBAN string (not fully validated)."""
    if country == "ES":
        bank_code = f"{random.randint(1000, 9999)}"
        branch = f"{random.randint(1000, 9999)}"
        account = f"{random.randint(1000000000, 9999999999)}"
        return f"{country}00 {bank_code} {branch} 00 {account}"
    account = "".join(random.choices(string.digits, k=12))
    return f"{country}00 {account[:4]} {account[4:8]} {account[8:12]} {account[12:]}"


def generate_bank_statement(language: str, output_path: Path) -> BankStatement:
    """Generate a synthetic bank statement PDF for a given language.

    Returns:
        BankStatement: Ground truth data for the generated document.

    We randomize between three different layout structures so the resulting
    documents are visually and structurally diverse:

      - layout A: classic statement (header + account info table + 4-col tx table)
      - layout B: compact statement (minimal info + 3-col tx table)
      - layout C: summary-first statement (summary box + 4-col tx table)
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    if language == "es":
        bank = random.choice(SPANISH_BANKS)
        holder = f"{random.choice(SPANISH_NAMES)} {random.choice(SPANISH_SURNAMES)}"
        concepts = [
            "Transferencia recibida",
            "Pago con tarjeta",
            "Nómina",
            "Recibo luz",
            "Compra supermercado",
        ]
    elif language == "en":
        bank = random.choice(ENGLISH_BANKS)
        holder = f"{random.choice(ENGLISH_NAMES)} {random.choice(ENGLISH_SURNAMES)}"
        concepts = [
            "Transfer received",
            "Card payment",
            "Salary",
            "Electricity bill",
            "Supermarket purchase",
        ]
    else:  # ca
        bank = random.choice(SPANISH_BANKS)
        holder = f"{random.choice(CATALAN_NAMES)} {random.choice(CATALAN_SURNAMES)}"
        concepts = [
            "Transferència rebuda",
            "Pagament amb targeta",
            "Nòmina",
            "Rebut llum",
            "Compra supermercat",
        ]

    iban = generate_iban("ES" if language in {"es", "ca"} else "GB")
    start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = date.today().strftime("%Y-%m-%d")

    opening_balance = random.uniform(1000, 10000)
    balance = opening_balance
    transactions: list[list[str]] = []
    lineas_list = []

    for _ in range(random.randint(10, 20)):
        tx_date = (date.today() - timedelta(days=random.randint(0, 30))).strftime(
            "%Y-%m-%d"
        )
        concept = random.choice(concepts)
        amount = round(random.uniform(-500, 2000), 2)
        balance += amount
        transactions.append([tx_date, concept, f"{amount:.2f}", f"{balance:.2f}"])
        lineas_list.append(
            BankLine(
                fecha=tx_date,
                concepto=concept,
                importe=amount,
                saldo=balance,
            )
        )

    transactions.sort(key=lambda x: x[0])
    lineas_list.sort(key=lambda x: x.fecha)

    layout = random.choice(["A", "B", "C"])

    # Common header style
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=20,
    )
    title = {
        "es": "Extracto bancario",
        "en": "Bank Statement",
        "ca": "Extracte bancari",
    }[language]

    if layout == "A":
        # Classic layout: header + full account info + 4-column tx table.
        story.append(Paragraph(f"{bank} - {title}", title_style))
        story.append(Spacer(1, 0.3 * cm))

        if language == "es":
            info_data = [
                ["Titular:", holder],
                ["IBAN:", iban],
                ["Período:", f"{start_date} a {end_date}"],
            ]
        elif language == "ca":
            info_data = [
                ["Titular:", holder],
                ["IBAN:", iban],
                ["Període:", f"{start_date} a {end_date}"],
            ]
        else:
            info_data = [
                ["Account Holder:", holder],
                ["IBAN:", iban],
                ["Period:", f"{start_date} to {end_date}"],
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

        tx_header = ["Date", "Description", "Amount", "Balance"]
        tx_data = [tx_header]
        tx_data.extend(transactions)

        tx_table = Table(tx_data, colWidths=[3 * cm, 7 * cm, 2.5 * cm, 2.5 * cm])
        tx_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (2, 0), (3, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(tx_table)

    elif layout == "B":
        # Compact layout: minimal info, 3-column tx table (no running balance).
        compact_title = ParagraphStyle(
            "CompactTitle",
            parent=styles["Heading1"],
            fontSize=14,
            alignment=1,  # centered
            textColor=colors.HexColor("#222222"),
            spaceAfter=10,
        )
        story.append(Paragraph(f"{title} - {bank}", compact_title))

        # One-line account summary
        if language == "es" or language == "ca":
            summary_txt = f"{holder} · IBAN {iban} · {start_date} a {end_date}"
        else:
            summary_txt = f"{holder} · IBAN {iban} · {start_date} to {end_date}"
        story.append(Paragraph(summary_txt, styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))

        # 3-column table
        if language == "es":
            tx_header = ["Fecha", "Concepto", "Importe"]
        elif language == "ca":
            tx_header = ["Data", "Concepte", "Import"]
        else:
            tx_header = ["Date", "Description", "Amount"]

        tx_data = [tx_header]
        for row in transactions:
            tx_date, concept, amount_str, _bal_str = row
            tx_data.append([tx_date, concept, amount_str])

        tx_table = Table(tx_data, colWidths=[3 * cm, 9 * cm, 3 * cm])
        tx_table.setStyle(
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
        story.append(tx_table)

    else:
        # Layout C: summary box first, then classic 4-column table.
        story.append(Paragraph(f"{bank}", title_style))
        story.append(Paragraph(title, styles["Heading3"]))
        story.append(Spacer(1, 0.2 * cm))

        final_balance = float(transactions[-1][-1]) if transactions else opening_balance

        if language == "es":
            summary_data = [
                ["Titular", holder],
                ["IBAN", iban],
                ["Período", f"{start_date} a {end_date}"],
                ["Saldo inicial", f"{opening_balance:.2f} EUR"],
                ["Saldo final", f"{final_balance:.2f} EUR"],
            ]
        elif language == "ca":
            summary_data = [
                ["Titular", holder],
                ["IBAN", iban],
                ["Període", f"{start_date} a {end_date}"],
                ["Saldo inicial", f"{opening_balance:.2f} EUR"],
                ["Saldo final", f"{final_balance:.2f} EUR"],
            ]
        else:
            summary_data = [
                ["Account Holder", holder],
                ["IBAN", iban],
                ["Period", f"{start_date} to {end_date}"],
                ["Opening balance", f"{opening_balance:.2f} EUR"],
                ["Closing balance", f"{final_balance:.2f} EUR"],
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
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 0.5 * cm))

        tx_header = ["Date", "Description", "Amount", "Balance"]
        tx_data = [tx_header]
        tx_data.extend(transactions)

        tx_table = Table(tx_data, colWidths=[3 * cm, 7 * cm, 2.5 * cm, 2.5 * cm])
        tx_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (2, 0), (3, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(tx_table)

    doc.build(story)

    # Create and return ground truth
    final_balance = float(transactions[-1][-1]) if transactions else opening_balance
    return BankStatement(
        banco=bank,
        titular=holder,
        iban=iban,
        periodo_desde=start_date,
        periodo_hasta=end_date,
        moneda="EUR",
        lineas=lineas_list,
        saldo_inicial=opening_balance,
        saldo_final=final_balance,
    )


def pdf_to_jpgs(pdf_path: Path, images_dir: Path) -> None:
    """Convert one PDF to JPGs at multiple qualities."""
    images_dir.mkdir(parents=True, exist_ok=True)
    try:
        pages = convert_from_path(str(pdf_path))
    except Exception as exc:  # pragma: no cover - defensive
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
    print("=" * 70)
    print("Synthetic Bank Dataset Generator (PDF + JPG)")
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
            pdf_path = pdf_dir / f"bank_{lang}_{i:02d}.pdf"
            ground_truth = generate_bank_statement(lang, pdf_path)
            print(f"[pdf] {pdf_path.relative_to(ROOT.parent)}")

            # Save ground truth
            gt_path = ground_truth_dir / f"bank_{lang}_{i:02d}_ground_truth.json"
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
