"""Delivery note-specific data models.

This module provides delivery note data models.
For extraction and visualization, use the unified functions:
- extract_document() from unified_extractor
- annotate_document_pdf() from unified_visualizer
"""

from .models import DeliveryNoteReport, ProductoLinea

__all__ = ["DeliveryNoteReport", "ProductoLinea"]
