"""OCR handling for CLI."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from PIL import Image


def extract_ocr_with_engine(
    doc_path: Path,
    ocr_engine: Any,
    file_type: str,
) -> dict[str, Any]:
    """Extract OCR using the specified engine.

    Args:
        doc_path: Path to the document file.
        ocr_engine: OCR engine instance.
        file_type: File type ("pdf" or "jpg"/"png"/"jpeg").

    Returns:
        Dictionary with OCR results in the expected format.
    """
    from pdf2image import convert_from_path

    t0 = time.perf_counter()
    pages = []

    if file_type == "pdf":
        # Convert PDF pages to images
        pdf_images = convert_from_path(str(doc_path), dpi=300)
        for page_idx, img in enumerate(pdf_images):
            page = ocr_engine.recognize_page(img, page_idx)
            pages.append(page)
    else:
        # Process single image
        img = Image.open(doc_path).convert("RGB")
        page = ocr_engine.recognize_page(img, 0)
        pages.append(page)

    total_runtime = time.perf_counter() - t0

    # Get engine config (store relevant args)
    engine_config = {
        "langs": ocr_engine.langs,
    }
    if hasattr(ocr_engine, "oem"):
        engine_config["tesseract_oem"] = ocr_engine.oem
        engine_config["tesseract_psm"] = ocr_engine.psm
        if ocr_engine.extra_cfg:
            engine_config["tesseract_extra"] = ocr_engine.extra_cfg

    # Convert pages to result format
    full_text = "\n\n".join(p.text for p in pages)

    # Convert words to ocr_items format
    ocr_items = []
    for page in pages:
        for word in page.words:
            ocr_items.append(
                {
                    "page_no": page.page_index + 1,  # Convert to 1-indexed
                    "text": word.text,
                    "bbox": {
                        "l": word.bbox[0],
                        "t": word.bbox[1],
                        "r": word.bbox[2],
                        "b": word.bbox[3],
                        "x0": word.bbox[0],
                        "y0": word.bbox[1],
                        "x1": word.bbox[2],
                        "y1": word.bbox[3],
                    },
                }
            )

    # Generate markdown (simple conversion from text)
    markdown = full_text.replace("\n\n", "\n\n")

    return {
        "text": full_text,
        "markdown": markdown,
        "ocr_items": ocr_items,
        "metadata": {
            "ocr": {
                "engine": ocr_engine.name,
                "engine_config": engine_config,
                "runtime_sec": total_runtime,
                "pages": [
                    {
                        "page_index": p.page_index,
                        "width": p.width,
                        "height": p.height,
                        "runtime_sec": p.runtime_sec,
                    }
                    for p in pages
                ],
            }
        },
    }
