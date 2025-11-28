#!/usr/bin/env python3
"""Batch inference script to process all documents and store results.

This script processes all documents in the data directory, runs OCR and extraction,
and saves results with visualizations to the outputs directory.

Usage:
    python -m tools.batch_inference.main --data-dir data --output-dir outputs
"""

from __future__ import annotations

import argparse

# Import OCR factory
import sys
from pathlib import Path

from .path_utils import determine_quality_and_type
from .processor import process_document

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from document_llm_extractor.ocr.factory import build_ocr_engine


def main() -> None:
    """Main entry point for batch inference."""
    parser = argparse.ArgumentParser(description="Batch inference for all documents")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing document data",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory to save inference results",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of documents to process (default: all)",
    )
    parser.add_argument(
        "--doc-type",
        type=str,
        default=None,
        choices=["deliverynote", "bank", "id", "payroll"],
        help="Process only specific document type (default: all types)",
    )
    parser.add_argument(
        "--ocr-engine",
        type=str,
        default=None,
        choices=["tesseract", "rapidocr"],
        help="OCR engine to use (default: rapidocr)",
    )
    parser.add_argument(
        "--langs",
        type=str,
        default="spa,cat,eng",
        help='Comma-separated list of OCR languages (e.g., "spa,cat,eng")',
    )
    parser.add_argument(
        "--tesseract-oem",
        type=int,
        default=1,
        help="Tesseract OCR Engine Mode (0-3, default: 1 for LSTM)",
    )
    parser.add_argument(
        "--tesseract-psm",
        type=int,
        default=6,
        help="Tesseract Page Segmentation Mode (0-13, default: 6 for uniform block)",
    )
    parser.add_argument(
        "--tesseract-extra",
        type=str,
        default="",
        help="Additional Tesseract configuration string",
    )
    args = parser.parse_args()

    data_dir = args.data_dir
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build OCR engine (default to rapidocr if not specified)
    ocr_engine_name = args.ocr_engine if args.ocr_engine else "rapidocr"
    langs_list = [s.strip() for s in args.langs.split(",") if s.strip()]
    engine_kwargs = {}

    if ocr_engine_name == "tesseract":
        engine_kwargs = {
            "oem": args.tesseract_oem,
            "psm": args.tesseract_psm,
            "extra_cfg": args.tesseract_extra,
        }
        ocr_engine = build_ocr_engine(
            ocr_engine_name, langs=langs_list, **engine_kwargs
        )
    elif ocr_engine_name == "rapidocr":
        ocr_engine = build_ocr_engine(
            ocr_engine_name, langs=langs_list, **engine_kwargs
        )
    else:
        raise ValueError(f"Unsupported OCR engine: {ocr_engine_name}")

    print(f"Using OCR engine: {ocr_engine_name}")
    if ocr_engine:
        print(f"Languages: {langs_list}")

    # Find all documents first
    doc_types = (
        [args.doc_type] if args.doc_type else ["deliverynote", "bank", "id", "payroll"]
    )
    langs = ["es", "en", "ca"]

    all_documents: list[tuple[Path, str, str, str, str]] = []

    for doc_type in doc_types:
        for lang in langs:
            # Collect PDFs
            pdf_dir = data_dir / doc_type / "pdf" / lang
            if pdf_dir.exists():
                for pdf_path in sorted(pdf_dir.glob("*.pdf")):
                    quality, file_type = determine_quality_and_type(pdf_path.name)
                    all_documents.append((pdf_path, doc_type, lang, quality, file_type))

            # Collect images
            img_dir = data_dir / doc_type / "images" / lang
            if img_dir.exists():
                for img_path in sorted(img_dir.glob("*.jpg")):
                    quality, file_type = determine_quality_and_type(img_path.name)
                    all_documents.append((img_path, doc_type, lang, quality, file_type))

    # Apply limit if specified
    if args.limit is not None:
        all_documents = all_documents[: args.limit]

    total_docs = len(all_documents)
    processed = 0
    failed = 0
    skipped = 0

    print("=" * 70)
    print("Batch Inference Pipeline")
    print("=" * 70)
    print(f"Data directory: {data_dir}")
    print(f"Output directory: {output_dir}")
    if args.doc_type:
        print(f"Document type filter: {args.doc_type}")
    if args.limit is not None:
        print(f"Processing limit: {args.limit} documents")
    print(f"Total documents found: {total_docs}")
    print()

    # Process documents one by one sequentially
    for idx, (doc_path, doc_type, lang, quality, file_type) in enumerate(
        all_documents, 1
    ):
        print(f"[{idx}/{total_docs}] Processing {doc_path.name}...")
        result = process_document(
            doc_path,
            doc_type,
            lang,
            quality,
            file_type,
            output_dir,
            ocr_engine=ocr_engine,
            ocr_engine_name=ocr_engine_name,
        )
        if result:
            if result.get("skipped"):
                skipped += 1
                print(f"[SKIP] Output already exists for {doc_path.name}")
            else:
                processed += 1
                print(f"[OK] Successfully processed {doc_path.name}")
        else:
            failed += 1
            print(f"[FAILED] Failed to process {doc_path.name}")

        # Try to free GPU memory between documents
        # Note: GPU memory management is handled by Docling internally

    print()
    print("=" * 70)
    print("Processing complete!")
    print(f"Total documents: {total_docs}")
    print(f"Processed successfully: {processed}")
    print(f"Skipped (already exists): {skipped}")
    print(f"Failed: {failed}")
    print("=" * 70)


if __name__ == "__main__":
    main()
