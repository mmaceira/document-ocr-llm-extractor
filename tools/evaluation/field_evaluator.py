"""Field-level evaluation functions."""

from __future__ import annotations

# Import text_normalize for token F1
import sys
from pathlib import Path
from typing import Any

from .comparators.arrays import compare_arrays
from .comparators.dates import compare_dates
from .comparators.numbers import compare_floats
from .comparators.strings import compare_strings

sys.path.insert(0, str(Path(__file__).parent.parent))
from text_normalize import token_f1


def compare_field(
    field_name: str,
    extracted_value: Any,
    ground_truth_value: Any,
    field_type: type | None = None,
) -> dict[str, Any]:
    """Compare a single field.

    Args:
        field_name: Name of the field.
        extracted_value: Extracted value.
        ground_truth_value: Ground truth value.
        field_type: Optional field type hint.

    Returns:
        Dictionary with field comparison results including token-level F1.
    """
    # Determine field type if not provided
    if field_type is None:
        if isinstance(ground_truth_value, float) or isinstance(extracted_value, float):
            field_type = float
        elif isinstance(ground_truth_value, list) or isinstance(extracted_value, list):
            field_type = list
        elif "date" in field_name.lower() or "fecha" in field_name.lower():
            field_type = str  # Will use date comparison
        else:
            field_type = str

    # Compare based on type
    if field_type is float:
        error_type, error_details = compare_floats(extracted_value, ground_truth_value)
    elif field_type is list:
        error_type, error_details = compare_arrays(
            extracted_value or [], ground_truth_value or [], field_name
        )
    elif "date" in field_name.lower() or "fecha" in field_name.lower():
        error_type, error_details = compare_dates(extracted_value, ground_truth_value)
    else:
        error_type, error_details = compare_strings(extracted_value, ground_truth_value)

    # Compute token-level F1 for string fields
    token_f1_score = None
    if (
        field_type is str
        and extracted_value is not None
        and ground_truth_value is not None
    ):
        pred_str = str(extracted_value)
        gt_str = str(ground_truth_value)
        _, _, f1 = token_f1(pred_str, gt_str)
        token_f1_score = f1

    # Determine field type category for error classification
    field_type_category = "string"
    if field_type is float:
        field_type_category = "amount"
    elif "date" in field_name.lower() or "fecha" in field_name.lower():
        field_type_category = "date"
    elif field_type is list:
        field_type_category = "list"

    # Determine error type category
    error_type_category = "exact_match"
    if error_type == "not_extracted":
        error_type_category = "empty"
    elif error_type == "minor_error":
        error_type_category = "format_mismatch"
    elif error_type == "major_error":
        error_type_category = "wrong_value"

    result = {
        "field_name": field_name,
        "status": error_type,
        "extracted_value": extracted_value,
        "ground_truth_value": ground_truth_value,
        "error_type": error_type,
        "error_details": error_details,
        "type": field_type_category,
        "error_type_category": error_type_category,
    }

    if token_f1_score is not None:
        result["token_f1"] = token_f1_score

    return result
