"""String comparison functions."""

from __future__ import annotations

from difflib import SequenceMatcher


def normalize_string(s: str) -> str:
    """Normalize string for comparison.

    Args:
        s: Input string.

    Returns:
        Normalized string (lowercased, whitespace collapsed).
    """
    if not isinstance(s, str):
        s = str(s)
    return " ".join(s.lower().split())


def fuzzy_match(str1: str, str2: str, threshold: float = 0.8) -> bool:
    """Check if two strings are similar using fuzzy matching.

    Args:
        str1: First string.
        str2: Second string.
        threshold: Similarity threshold (default: 0.8).

    Returns:
        True if strings are similar above threshold.
    """
    return (
        SequenceMatcher(None, normalize_string(str1), normalize_string(str2)).ratio()
        >= threshold
    )


def compare_strings(extracted: str | None, ground_truth: str | None) -> tuple[str, str]:
    """Compare two string values.

    Args:
        extracted: Extracted string value.
        ground_truth: Ground truth string value.

    Returns:
        Tuple of (error_type, error_details).
    """
    if extracted is None and ground_truth is None:
        return "exact_match", ""

    if extracted is None:
        return "not_extracted", ""

    if ground_truth is None:
        return "major_error", "Extracted value when should be None"

    extracted_str = str(extracted)
    ground_truth_str = str(ground_truth)

    if normalize_string(extracted_str) == normalize_string(ground_truth_str):
        return "exact_match", ""

    # Check for minor errors (fuzzy match)
    if fuzzy_match(extracted_str, ground_truth_str, threshold=0.8):
        return (
            "minor_error",
            f"Extracted: '{extracted_str}' vs Ground truth: '{ground_truth_str}'",
        )

    return (
        "major_error",
        f"Extracted: '{extracted_str}' vs Ground truth: '{ground_truth_str}'",
    )
