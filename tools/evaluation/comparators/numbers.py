"""Numeric comparison functions."""

from __future__ import annotations

from typing import Any


def compare_floats(
    extracted: Any, ground_truth: Any, tolerance: float = 0.01
) -> tuple[str, str]:
    """Compare two float values.

    Args:
        extracted: Extracted float value.
        ground_truth: Ground truth float value.
        tolerance: Absolute tolerance for exact match (default: 0.01).

    Returns:
        Tuple of (error_type, error_details).
    """
    if extracted is None and ground_truth is None:
        return "exact_match", ""

    if extracted is None:
        return "not_extracted", ""

    if ground_truth is None:
        return "major_error", "Extracted value when should be None"

    try:
        ext_val = float(extracted)
        gt_val = float(ground_truth)

        diff = abs(ext_val - gt_val)
        if diff <= tolerance:
            return "exact_match", ""

        # Check for minor errors (within 5% tolerance)
        if gt_val != 0:
            percent_diff = abs(diff / gt_val)
            if percent_diff <= 0.05:
                return (
                    "minor_error",
                    f"Extracted: {ext_val} vs Ground truth: {gt_val} (diff: {diff:.2f})",
                )

        return (
            "major_error",
            f"Extracted: {ext_val} vs Ground truth: {gt_val} (diff: {diff:.2f})",
        )
    except (ValueError, TypeError):
        ext_type = type(extracted).__name__
        gt_type = type(ground_truth).__name__
        return (
            "major_error",
            f"Type mismatch: extracted={ext_type}, ground_truth={gt_type}",
        )
