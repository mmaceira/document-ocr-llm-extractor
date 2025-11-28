"""Path and file type utility functions."""

from __future__ import annotations

from pathlib import Path


def determine_doc_type_and_lang(path: Path) -> tuple[str, str] | None:
    """Determine document type and language from path.

    Args:
        path: Path to the document file.

    Returns:
        Tuple of (doc_type, lang) or None if cannot determine.
    """
    parts = path.parts
    if "data" not in parts:
        return None

    data_idx = parts.index("data")
    if data_idx + 1 >= len(parts):
        return None

    doc_type = parts[data_idx + 1]
    if doc_type not in {"deliverynote", "bank", "id", "payroll"}:
        return None

    # Find language (should be in path after pdf/images)
    lang = None
    for part in parts:
        if part in {"es", "en", "ca"}:
            lang = part
            break

    if lang is None:
        return None

    return doc_type, lang


def determine_quality_and_type(filename: str) -> tuple[str, str]:
    """Determine quality and file type from filename.

    Args:
        filename: Name of the file.

    Returns:
        Tuple of (quality, file_type).
    """
    if filename.endswith(".pdf"):
        return "best", "pdf"
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        if "_q10" in filename:
            return "bad", "jpg"
        if "_q40" in filename:
            return "medium", "jpg"
        if "_q90" in filename:
            return "good", "jpg"
        return "good", "jpg"  # Default for images without quality marker
    return "unknown", "unknown"
