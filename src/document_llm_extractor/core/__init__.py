"""Generic framework for document extraction pipelines.

This module provides reusable components for any document extraction pipeline:
- OCR extraction using Docling
- LLM-based structured data extraction
- PDF visualization with OCR annotations
"""

from .extractor import extract_structured_data
from .ocr import extract_ocr
from .visualizer import annotate_pdf

__all__ = ["extract_ocr", "extract_structured_data", "annotate_pdf"]
