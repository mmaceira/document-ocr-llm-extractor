"""Main CLI entry point."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import uuid
from pathlib import Path

from ..document_config import DOCUMENT_CONFIGS
from ..ocr import build_ocr_engine
from ..settings import SETTINGS
from ..unified_extractor import extract_document
from ..unified_visualizer import annotate_document_pdf
from .ocr_handler import extract_ocr_with_engine


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point for document extraction pipeline.

    Processes a PDF or image document through the complete pipeline:
    1. OCR extraction (RapidOCR by default, or Tesseract/Docling)
    2. LLM-based structured data extraction
    3. PDF visualization with OCR boxes and legend

    Outputs are saved to a timestamped directory structure:
    - {output_dir}/{run_id}/raw/ - OCR text, markdown, and JSON
    - {output_dir}/{run_id}/llm/ - LLM extraction results and debug info
    - {output_dir}/{run_id}/viz/ - Annotated PDF with visualization

    Args:
        argv: Optional command-line arguments (defaults to sys.argv).

    Exit codes:
        0: Success
        2: Document file not found
        Other: Runtime errors during processing
    """
    parser = argparse.ArgumentParser("document-llm-extractor")
    parser.add_argument("input_doc", type=Path, help="Input PDF or image file")
    parser.add_argument(
        "--doc-type",
        choices=list(DOCUMENT_CONFIGS.keys()),
        default="deliverynote",
        help="Document type to extract",
    )
    parser.add_argument("--output-dir", default=SETTINGS.outputs_dir)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--redact", action="store_true", default=SETTINGS.redact_output)
    parser.add_argument(
        "--ocr-engine",
        type=str,
        default="rapidocr",
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
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    input_path = args.input_doc

    if not input_path.exists():
        print(f"ERROR: Document not found: {input_path}", file=sys.stderr)
        sys.exit(2)

    # Determine file type
    suffix = input_path.suffix.lower()
    if suffix == ".pdf":
        file_type = "pdf"
    elif suffix in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]:
        file_type = "image"
    else:
        print(f"ERROR: Unsupported file type: {suffix}", file=sys.stderr)
        print("Supported: .pdf, .jpg, .jpeg, .png, .bmp, .tiff, .tif", file=sys.stderr)
        sys.exit(2)

    # Setup output directory
    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
    out_dir = output_root / run_id
    (out_dir / "raw").mkdir(parents=True, exist_ok=True)
    (out_dir / "llm").mkdir(parents=True, exist_ok=True)
    (out_dir / "viz").mkdir(parents=True, exist_ok=True)
    base_name = input_path.stem

    # 1) OCR
    langs_list = [lang.strip() for lang in args.langs.split(",") if lang.strip()]
    engine_kwargs = {}
    if args.ocr_engine == "tesseract":
        engine_kwargs["oem"] = args.tesseract_oem
        engine_kwargs["psm"] = args.tesseract_psm
        if args.tesseract_extra:
            engine_kwargs["extra_cfg"] = args.tesseract_extra

    try:
        ocr_engine = build_ocr_engine(args.ocr_engine, langs_list, **engine_kwargs)
    except ImportError as e:
        print(
            f"ERROR: Failed to import {args.ocr_engine} OCR engine: {e}",
            file=sys.stderr,
        )
        if args.ocr_engine == "tesseract":
            print(
                "Install pytesseract with: pip install pytesseract",
                file=sys.stderr,
            )
            print(
                "Install Tesseract binary with: sudo apt-get install tesseract-ocr",
                file=sys.stderr,
            )
        elif args.ocr_engine == "rapidocr":
            print(
                "Install rapidocr-onnxruntime with: pip install rapidocr-onnxruntime",
                file=sys.stderr,
            )
        sys.exit(2)

    try:
        ocr = extract_ocr_with_engine(input_path, ocr_engine, file_type)
    except Exception as e:
        # Catch TesseractNotFoundError and other runtime errors
        error_type = type(e).__name__
        error_msg = str(e)

        # Try to import pytesseract to check for TesseractNotFoundError type
        try:
            import pytesseract

            TesseractNotFoundError = pytesseract.TesseractNotFoundError
        except (ImportError, AttributeError):
            TesseractNotFoundError = None

        # Check for TesseractNotFoundError (exception type or as string)
        is_tesseract_error = (
            (TesseractNotFoundError and isinstance(e, TesseractNotFoundError))
            or error_type == "TesseractNotFoundError"
            or "TesseractNotFoundError" in error_msg
            or "tesseract is not installed" in error_msg.lower()
            or "tesseract not found" in error_msg.lower()
            or "tesseract binary is not installed" in error_msg.lower()
        )

        if is_tesseract_error and args.ocr_engine == "tesseract":
            print(
                "ERROR: Tesseract binary is not installed or not in PATH.",
                file=sys.stderr,
            )
            print(
                "Install Tesseract with: sudo apt-get install "
                "tesseract-ocr tesseract-ocr-spa tesseract-ocr-cat tesseract-ocr-eng",
                file=sys.stderr,
            )
            print(
                "Or use --ocr-engine rapidocr instead.",
                file=sys.stderr,
            )
        else:
            print(
                f"ERROR: OCR processing failed: {error_msg}",
                file=sys.stderr,
            )
            if args.ocr_engine == "tesseract":
                print(
                    "Hint: If Tesseract is not installed, use --ocr-engine rapidocr instead.",
                    file=sys.stderr,
                )
        sys.exit(1)

    (out_dir / "raw" / f"{base_name}.txt").write_text(ocr["text"], encoding="utf-8")
    if "markdown" in ocr:
        (out_dir / "raw" / f"{base_name}.md").write_text(
            ocr["markdown"], encoding="utf-8"
        )
    (out_dir / "raw" / f"{base_name}_ocr.json").write_text(
        json.dumps(ocr["ocr_items"], ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 2) LLM extraction (unified)
    report = extract_document(args.doc_type, ocr["text"], debug_dir=out_dir / "llm")
    output_filename = f"{args.doc_type}.json"
    (out_dir / "llm" / output_filename).write_text(
        json.dumps(report.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 3) Visualization (unified)
    # The visualizer automatically handles both PDFs and images
    pdf_out = out_dir / "viz" / f"{base_name}_viz.pdf"
    annotate_document_pdf(
        doc_type=args.doc_type,
        input_pdf=input_path,  # Can be PDF or image - visualizer handles both
        report=report,
        ocr_items=ocr["ocr_items"],
        output_pdf=pdf_out,
        redact=args.redact,
        ocr_metadata=ocr.get("metadata"),
    )

    # 4) Output JSON
    data = report.model_dump()
    if args.pretty:
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    else:
        json.dump(data, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")

    print(f"\nRun: {run_id}\nPDF: {pdf_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
