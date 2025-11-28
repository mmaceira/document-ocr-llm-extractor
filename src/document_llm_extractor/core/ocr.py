"""OCR extraction using Docling for text and bounding boxes from PDFs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    OcrAutoOptions,
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

from ..settings import SETTINGS


def build_converter() -> DocumentConverter:
    """Build DocumentConverter with OCR settings from configuration."""
    opts = PdfPipelineOptions()
    opts.do_ocr = True
    opts.do_table_structure = False
    opts.images_scale = SETTINGS.images_scale
    # Note: do_deskew and do_binarization are not available in current Docling version
    # opts.do_deskew = SETTINGS.deskew
    # opts.do_binarization = SETTINGS.binarize
    if SETTINGS.max_pages is not None:
        opts.max_pages = SETTINGS.max_pages

    ocr_opts = OcrAutoOptions()
    ocr_langs = [lang.strip() for lang in SETTINGS.ocr_langs.split(",") if lang.strip()]
    if ocr_langs:
        ocr_opts.lang = ocr_langs
    opts.ocr_options = ocr_opts

    accel = AcceleratorOptions(
        device=AcceleratorDevice.GPU if SETTINGS.docling_gpu else AcceleratorDevice.CPU
    )

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=opts, accelerator_options=accel
            )
        }
    )


def _split_large_ocr_item(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Split large OCR items containing multiple fields into separate items."""
    text = item.get("text", "").strip()
    bbox = item.get("bbox", {})
    page_no = item.get("page_no", 1)

    # Don't split if text is short
    if len(text) < 30:
        return [item]

    # Check if text contains multiple fields (colons, pipes, or common patterns)
    colon_count = text.count(":")
    pipe_count = text.count("|")

    # Need at least 2 colons or 1 pipe to consider splitting
    if colon_count < 2 and pipe_count == 0:
        return [item]

    # Split by common separators
    parts = []

    # First, try splitting by "|" if present (e.g., "Field|Value Field|Value")
    if pipe_count > 0:
        parts = [p.strip() for p in text.split("|") if p.strip()]
    elif colon_count >= 2:
        # Split by field-value patterns: "Field: Value" followed by space and next field
        # Pattern matches: "FieldName: Value" (where Value can contain spaces)
        # Look for patterns like "Numero Delivery Note: DN-54288 Fecha: 2025-11-27"
        pattern = r"([A-Za-zÁÉÍÓÚáéíóúÑñ\s/]+:\s*[^\s:]+(?:\s+[^\s:]+)*)"
        matches = re.findall(pattern, text)
        if len(matches) > 1:
            parts = [m.strip() for m in matches if m.strip()]
        else:
            # Fallback: split by multiple consecutive spaces (likely field separators)
            parts = re.split(r"\s{2,}", text)
            parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]

    # If we couldn't split meaningfully, return original
    if len(parts) <= 1:
        return [item]

    # Calculate bounding box dimensions
    left = bbox.get("l") or bbox.get("x0", 0.0)
    top = bbox.get("t") or bbox.get("y0", 0.0)
    right = bbox.get("r") or bbox.get("x1", 0.0)
    bottom = bbox.get("b") or bbox.get("y1", 0.0)

    bbox_width = right - left
    bbox_height = bottom - top

    # Create split items with proportional bounding boxes
    split_items = []
    current_pos = 0

    for part in parts:
        if not part.strip():
            continue

        # Find position of this part in the original text
        part_start = text.find(part, current_pos)
        if part_start == -1:
            part_start = current_pos
        part_end = part_start + len(part)
        current_pos = max(part_end, current_pos + 1)  # Avoid infinite loops

        # Calculate proportional bounding box based on text position
        total_length = len(text)
        if total_length == 0:
            continue

        part_start_ratio = part_start / total_length
        part_end_ratio = part_end / total_length

        # Estimate horizontal position (assuming left-to-right text)
        part_left = left + (bbox_width * part_start_ratio)
        part_right = left + (bbox_width * part_end_ratio)

        # For vertical positioning, estimate based on number of parts
        # If we have many parts, they might be on different lines
        num_parts = len(parts)
        if num_parts > 3 and bbox_height > bbox_width * 0.5:
            # Likely multi-line: distribute vertically
            part_index = parts.index(part)
            lines_estimate = min(
                num_parts, max(1, int(bbox_height / (bbox_width * 0.1)))
            )
            line_height = bbox_height / lines_estimate
            line_num = min(part_index, lines_estimate - 1)
            part_top = top + (line_num * line_height)
            part_bottom = part_top + line_height
        else:
            # Single line or horizontal layout: use same vertical bounds
            part_top = top
            part_bottom = bottom

        split_items.append(
            {
                "page_no": page_no,
                "text": part.strip(),
                "bbox": {
                    "l": part_left,
                    "t": part_top,
                    "r": part_right,
                    "b": part_bottom,
                    "coord_origin": bbox.get("coord_origin", "BOTTOMLEFT"),
                },
            }
        )

    return split_items if len(split_items) > 1 else [item]


def extract_ocr(pdf_path: Path | str) -> dict[str, Any]:
    """Extract OCR text and bounding boxes from PDF.

    Returns dict with "text", "markdown", and "ocr_items" (list of items with page_no, text, bbox).
    """
    pdf_path = Path(pdf_path)
    converter = build_converter()
    result = converter.convert(str(pdf_path))
    doc = result.document

    # Extract OCR items
    ocr_items = []
    doc_dict = doc.export_to_dict()
    for text_item in doc_dict.get("texts", []):
        if not isinstance(text_item, dict):
            continue
        text_content = text_item.get("text") or text_item.get("orig") or ""
        if not text_content:
            continue
        for prov in text_item.get("prov", []):
            if isinstance(prov, dict) and prov.get("page_no") is not None:
                item = {
                    "page_no": int(prov["page_no"]),
                    "text": text_content.strip(),
                    "bbox": prov.get("bbox", {}),
                }
                # Split large items into smaller ones for better visualization
                split_items = _split_large_ocr_item(item)
                ocr_items.extend(split_items)

    return {
        "markdown": doc.export_to_markdown(),
        "text": doc.export_to_text(),
        "ocr_items": ocr_items,
    }
