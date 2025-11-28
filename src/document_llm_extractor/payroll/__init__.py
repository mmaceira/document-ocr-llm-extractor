"""Payroll document data models.

This module provides payroll (nómina) data models.
For extraction and visualization, use the unified functions:
- extract_document() from unified_extractor
- annotate_document_pdf() from unified_visualizer
"""

from .models import Deduccion, Devengo, PayrollReport

__all__ = [
    "PayrollReport",
    "Devengo",
    "Deduccion",
]
