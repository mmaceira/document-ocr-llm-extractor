"""Array comparison functions."""

from __future__ import annotations

from typing import Any


def compare_arrays(
    extracted: list[Any], ground_truth: list[Any], field_name: str
) -> tuple[str, str]:
    """Compare two arrays.

    Args:
        extracted: Extracted array.
        ground_truth: Ground truth array.
        field_name: Name of the field being compared (for error messages).

    Returns:
        Tuple of (error_type, error_details).
    """
    if not extracted and not ground_truth:
        return "exact_match", ""

    if not extracted:
        return "not_extracted", ""

    if not ground_truth:
        return "major_error", "Extracted array when should be empty"

    if len(extracted) != len(ground_truth):
        return (
            "major_error",
            f"Length mismatch: extracted={len(extracted)}, ground_truth={len(ground_truth)}",
        )

    # For now, just check length match
    # More sophisticated comparison could be added
    return "exact_match", ""
