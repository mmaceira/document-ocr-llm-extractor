#!/usr/bin/env python3
"""
Benchmark script to compare OCR engine performance in Docling.
Tests: auto, tesseract, rapidocr, easyocr
"""

import sys
import time
from pathlib import Path

# Add tools to path for OCR metrics
sys.path.insert(0, str(Path(__file__).parent / "tools"))
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    EasyOcrOptions,
    OcrAutoOptions,
    PdfPipelineOptions,
    RapidOcrOptions,
    TesseractOcrOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from ocr_metrics import cer, wer


def test_ocr_engine(
    pdf_path: Path, ocr_options, engine_name: str, gt_text: str | None = None
):
    """Test a specific OCR engine and return timing and result.

    Args:
        pdf_path: Path to PDF file
        ocr_options: OCR options for the engine
        engine_name: Name of the OCR engine
        gt_text: Optional ground truth text for CER/WER calculation
    """
    pdf_opts = PdfPipelineOptions()
    pdf_opts.do_ocr = True
    pdf_opts.do_table_structure = False
    pdf_opts.ocr_options = ocr_options

    # Set languages based on engine type (different engines use different codes)
    if engine_name == "tesseract":
        pdf_opts.ocr_options.lang = ["spa", "eng", "cat"]  # Tesseract uses ISO 639-2/3
    elif engine_name == "rapidocr":
        pdf_opts.ocr_options.lang = ["spanish", "english"]  # RapidOCR uses full names
    elif engine_name == "easyocr":
        pdf_opts.ocr_options.lang = ["es", "en"]  # EasyOCR uses ISO 639-1
    else:  # auto
        pdf_opts.ocr_options.lang = ["spa", "eng", "cat"]  # Default to Tesseract format

    accel = AcceleratorOptions(device=AcceleratorDevice.CPU)

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pdf_opts, accelerator_options=accel
            )
        }
    )

    start_time = time.time()
    try:
        result = converter.convert(str(pdf_path))
        doc = result.document
        text = doc.export_to_text()
        elapsed = time.time() - start_time

        result_dict = {
            "engine": engine_name,
            "success": True,
            "time": elapsed,
            "text_length": len(text),
            "text_preview": text[:200] if text else "",
        }

        # Compute CER/WER if ground truth is available
        if gt_text and text:
            try:
                result_dict["cer"] = cer(gt_text, text)
                result_dict["wer"] = wer(gt_text, text)
            except Exception as e:
                print(f"[WARNING] Failed to compute CER/WER: {e}")

        return result_dict
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "engine": engine_name,
            "success": False,
            "time": elapsed,
            "error": str(e),
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark OCR engines")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("sample_data/sample_0001.pdf"),
        help="Path to PDF file",
    )
    parser.add_argument(
        "--gt-text",
        type=Path,
        default=None,
        help="Path to ground truth text file (optional, for CER/WER)",
    )
    args = parser.parse_args()

    pdf_path = args.pdf
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        return

    gt_text = None
    if args.gt_text and args.gt_text.exists():
        gt_text = args.gt_text.read_text(encoding="utf-8")
        print(f"Loaded ground truth text ({len(gt_text)} chars)")

    engines = [
        ("auto", OcrAutoOptions()),
        ("tesseract", TesseractOcrOptions()),
        ("rapidocr", RapidOcrOptions()),
        ("easyocr", EasyOcrOptions()),
    ]

    results = []
    for engine_name, ocr_opts in engines:
        print(f"\nTesting {engine_name}...")
        result = test_ocr_engine(pdf_path, ocr_opts, engine_name, gt_text)
        results.append(result)
        if result["success"]:
            msg = (
                f"  ✓ Success in {result['time']:.2f}s ({result['text_length']} chars)"
            )
            if "cer" in result:
                msg += f" | CER: {result['cer']:.3f}, WER: {result['wer']:.3f}"
            print(msg)
        else:
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)
    header = f"{'Engine':<15} {'Status':<10} {'Time (s)':<12} {'Text Length':<15}"
    if any("cer" in r for r in results if r.get("success")):
        header += f" {'CER':<10} {'WER':<10}"
    print(header)
    print("-" * 80)
    for r in results:
        status = "✓ OK" if r["success"] else "✗ FAIL"
        time_str = f"{r['time']:.2f}" if r["success"] else "N/A"
        length_str = str(r.get("text_length", "N/A")) if r["success"] else "N/A"
        row = f"{r['engine']:<15} {status:<10} {time_str:<12} {length_str:<15}"
        if "cer" in r:
            row += f" {r['cer']:<10.3f} {r['wer']:<10.3f}"
        print(row)

    # Find fastest successful engine
    successful = [r for r in results if r["success"]]
    if successful:
        fastest = min(successful, key=lambda x: x["time"])
        print(f"\nFastest engine: {fastest['engine']} ({fastest['time']:.2f}s)")

        # Find best CER/WER if available
        if any("cer" in r for r in successful):
            best_cer = min(
                (r for r in successful if "cer" in r), key=lambda x: x["cer"]
            )
            best_wer = min(
                (r for r in successful if "wer" in r), key=lambda x: x["wer"]
            )
            print(f"Best CER: {best_cer['engine']} (CER: {best_cer['cer']:.3f})")
            print(f"Best WER: {best_wer['engine']} (WER: {best_wer['wer']:.3f})")


if __name__ == "__main__":
    main()
