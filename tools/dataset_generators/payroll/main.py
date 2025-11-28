#!/usr/bin/env python3
"""Generate synthetic payroll (nómina / payslip) PDFs and JPGs.

Layout:
  data/
    payroll/
      pdf/{es,en,ca}/*.pdf
      images/{es,en,ca}/*_p<page>_q<quality>.jpg

JPEG qualities (good → bad): 90, 40, 10.
"""

from __future__ import annotations

import json
from pathlib import Path

from .constants import LANGS, SAMPLES_PER_LANG
from .converter import pdf_to_jpgs
from .generator import generate_payroll_pdf

ROOT = Path("data") / "payroll"
PDF_ROOT = ROOT / "pdf"
IMAGES_ROOT = ROOT / "images"
GROUND_TRUTH_ROOT = ROOT / "ground_truth"


def main() -> None:
    """Main entry point for payroll dataset generation."""
    print("=" * 70)
    print("Synthetic Payroll Dataset Generator (PDF + JPG)")
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
            pdf_path = pdf_dir / f"payroll_{lang}_{i:02d}.pdf"
            ground_truth = generate_payroll_pdf(lang, pdf_path)
            print(f"[pdf] {pdf_path.relative_to(ROOT.parent)}")

            # Save ground truth
            gt_path = ground_truth_dir / f"payroll_{lang}_{i:02d}_ground_truth.json"
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
