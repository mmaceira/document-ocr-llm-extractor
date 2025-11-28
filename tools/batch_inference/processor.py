"""Document processing functions."""

from __future__ import annotations

import json

# Import core modules
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from document_llm_extractor.cli.ocr_handler import extract_ocr_with_engine
from document_llm_extractor.unified_extractor import extract_document
from document_llm_extractor.unified_visualizer import annotate_document_pdf


def process_document(
    doc_path: Path,
    doc_type: str,
    lang: str,
    quality: str,
    file_type: str,
    output_dir: Path,
    ocr_engine: Any | None = None,
    ocr_engine_name: str | None = None,
) -> dict[str, Any] | None:
    """Process a single document through OCR and extraction.

    Args:
        doc_path: Path to the document file.
        doc_type: Document type (deliverynote, bank, id, payroll).
        lang: Language (es, en, ca).
        quality: Quality level (bad, medium, good, best).
        file_type: File type (pdf, jpg).
        output_dir: Base output directory.
        ocr_engine: Optional OCR engine instance.
        ocr_engine_name: Optional OCR engine name.

    Returns:
        Dictionary with results or None if processing failed.
    """
    try:
        # Create output directory structure: outputs/{ocr_engine}/inference/{doc_type}/{lang}
        # Default to "rapidocr" if no engine specified
        engine_name = ocr_engine_name if ocr_engine_name else "rapidocr"
        out_doc_dir = output_dir / engine_name / "inference" / doc_type / lang
        out_doc_dir.mkdir(parents=True, exist_ok=True)

        base_name = doc_path.stem
        # For images, preserve quality information in the filename
        # Format: {base}_p{page}_q{quality} -> {base}_q{quality}
        if file_type == "jpg" and "_p" in base_name:
            # Extract quality from filename
            # e.g., deliverynote_es_01_p1_q90 -> deliverynote_es_01_q90
            parts = base_name.split("_p")
            if len(parts) == 2:
                # parts[0] is the base, parts[1] contains page and quality
                page_quality = parts[1]
                if "_q" in page_quality:
                    quality_part = page_quality.split("_q")[1]  # Extract q90, q40, etc.
                    base_name = f"{parts[0]}_q{quality_part}"
                else:
                    # Fallback: keep original if format is unexpected
                    base_name = base_name.replace("_p", "_")

        # Check if output already exists - skip if it does
        result_path = out_doc_dir / f"{base_name}.json"
        if result_path.exists():
            # Return a special marker to indicate skip (not failure)
            return {"skipped": True}

        # Run OCR with error handling
        try:
            if ocr_engine is None:
                raise ValueError("OCR engine must be provided")
            ocr_result = extract_ocr_with_engine(doc_path, ocr_engine, file_type)
        except Exception as e:
            error_msg = str(e)
            # Handle CUDA memory errors - these are often fatal and need manual intervention
            if (
                "CUDA" in error_msg
                or "out of memory" in error_msg.lower()
                or "cudaErrorMemoryAllocation" in error_msg
            ):
                print(f"[ERROR] CUDA memory error for {doc_path.name}")
                print("       This usually means GPU memory is exhausted. Consider:")
                print("       - Processing fewer documents at once")
                print("       - Using CPU mode (set DOCLING_GPU=false)")
                print("       - Freeing GPU memory")
                return None
            print(f"[ERROR] Failed OCR for {doc_path.name}: {error_msg[:200]}")
            return None

        # Run extraction
        try:
            report = extract_document(doc_type, ocr_result["text"])
        except Exception as e:
            print(f"[ERROR] Failed extraction for {doc_path}: {e}")
            return None

        # Create visualization
        # Use annotate_document_pdf for both PDFs and images (same as CLI)
        # This ensures consistent behavior and proper coordinate handling
        viz_path = out_doc_dir / f"{base_name}_viz.pdf"
        try:
            annotate_document_pdf(
                doc_type=doc_type,
                input_pdf=doc_path,  # Can be PDF or image - visualizer handles both
                report=report,
                ocr_items=ocr_result["ocr_items"],
                output_pdf=viz_path,
                ocr_metadata=ocr_result.get("metadata"),
            )
            # Also create a JPG version for consistency
            from pdf2image import convert_from_path

            pages = convert_from_path(str(viz_path))
            if pages:
                viz_jpg_path = out_doc_dir / f"{base_name}_viz.jpg"
                pages[0].save(viz_jpg_path, "JPEG", quality=95)
        except Exception as e:
            import traceback

            print(f"[WARNING] Failed visualization for {doc_path}: {e}")
            print(f"[WARNING] Traceback: {traceback.format_exc()}")

        # Save results
        result = {
            "doc_type": doc_type,
            "lang": lang,
            "quality": quality,
            "file_type": file_type,
            "source_file": str(doc_path),
            "extracted_data": report.model_dump(),
            "ocr_text": ocr_result["text"],
            "ocr_items": ocr_result["ocr_items"],
        }
        # Add OCR metadata if present
        if "metadata" in ocr_result:
            result["metadata"] = ocr_result["metadata"]

        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return result

    except Exception as e:
        print(f"[ERROR] Failed to process {doc_path}: {e}")
        import traceback

        traceback.print_exc()
        return None
