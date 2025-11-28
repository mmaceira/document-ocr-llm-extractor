"""Date comparison functions."""

from __future__ import annotations

from typing import Any

from .strings import normalize_string


def compare_dates(extracted: Any, ground_truth: Any) -> tuple[str, str]:
    """Compare two date strings.

    Args:
        extracted: Extracted date string.
        ground_truth: Ground truth date string.

    Returns:
        Tuple of (error_type, error_details).
    """
    if extracted is None and ground_truth is None:
        return "exact_match", ""

    if extracted is None:
        return "not_extracted", ""

    if ground_truth is None:
        return "major_error", "Extracted value when should be None"

    # Normalize date strings (remove time if present)
    ext_str = str(extracted).split()[0] if " " in str(extracted) else str(extracted)
    gt_str = (
        str(ground_truth).split()[0] if " " in str(ground_truth) else str(ground_truth)
    )

    if normalize_string(ext_str) == normalize_string(gt_str):
        return "exact_match", ""

    # Check for minor errors (same date, different format)
    if ext_str.replace("-", "").replace("/", "") == gt_str.replace("-", "").replace(
        "/", ""
    ):
        return (
            "minor_error",
            f"Extracted: '{ext_str}' vs Ground truth: '{gt_str}' (format difference)",
        )

    return "major_error", f"Extracted: '{ext_str}' vs Ground truth: '{gt_str}'"
