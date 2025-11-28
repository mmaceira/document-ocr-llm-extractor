"""PDF to JPG conversion functions."""

from __future__ import annotations

from pathlib import Path

from pdf2image import convert_from_path

from .constants import QUALITIES

ROOT = Path("data") / "payroll"


def pdf_to_jpgs(pdf_path: Path, images_dir: Path) -> None:
    """Convert one PDF to JPGs at multiple qualities.

    Args:
        pdf_path: Path to the PDF file.
        images_dir: Directory to save JPG images.
    """
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
