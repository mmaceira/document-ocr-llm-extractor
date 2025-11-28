"""Document-level evaluation functions."""

from __future__ import annotations

# Import table_metrics for line-item evaluation
import sys
from pathlib import Path
from typing import Any

from .field_evaluator import compare_field

sys.path.insert(0, str(Path(__file__).parent.parent))
from table_metrics import line_items_scores


def evaluate_document(
    extracted_data: dict[str, Any],
    ground_truth_data: dict[str, Any],
    doc_type: str,
) -> dict[str, Any]:
    """Evaluate extracted data against ground truth.

    Args:
        extracted_data: Extracted document data.
        ground_truth_data: Ground truth document data.
        doc_type: Document type identifier.

    Returns:
        Dictionary with evaluation results.
    """
    # Import here to avoid circular dependencies
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from document_llm_extractor.document_config import get_config

    field_results = []

    # Get model class to know all fields
    try:
        config = get_config(doc_type)
    except ValueError as e:
        return {"error": str(e)}

    model_class = config.model_class
    model_fields = model_class.model_fields

    # Compare each field
    for field_name, _field_info in model_fields.items():
        extracted_value = extracted_data.get(field_name)
        ground_truth_value = ground_truth_data.get(field_name)

        # Handle nested structures (arrays of models) - use line-item metrics
        if field_name in {"productos", "lineas", "devengos", "deducciones"}:
            ext_list = extracted_value or []
            gt_list = ground_truth_value or []

            # Compute line-item metrics
            line_item_metrics = line_items_scores(gt_list, ext_list)

            # Determine status based on F1
            if line_item_metrics["items_f1"] == 1.0:
                status = "exact_match"
                error_type = "exact_match"
            elif (
                line_item_metrics["items_f1"] >= 0.8
                or line_item_metrics["matched_items"] > 0
            ):
                status = "minor_error"
                error_type = "minor_error"
            else:
                status = "major_error"
                error_type = "major_error"

            field_results.append(
                {
                    "field_name": field_name,
                    "status": status,
                    "extracted_value": len(ext_list),
                    "ground_truth_value": len(gt_list),
                    "error_type": error_type,
                    "error_details": (
                        f"Matched {line_item_metrics['matched_items']}/{len(gt_list)} items. "
                        f"F1: {line_item_metrics['items_f1']:.3f}"
                    ),
                    "type": "list",
                    "error_type_category": (
                        "wrong_value" if status == "major_error" else "format_mismatch"
                    ),
                    "line_item_metrics": line_item_metrics,
                }
            )
        else:
            # Regular field comparison
            field_result = compare_field(
                field_name, extracted_value, ground_truth_value
            )
            field_results.append(field_result)

    # Calculate summary statistics
    total_fields = len(field_results)
    extracted_count = sum(1 for r in field_results if r["extracted_value"] is not None)
    exact_match_count = sum(1 for r in field_results if r["status"] == "exact_match")
    minor_error_count = sum(1 for r in field_results if r["status"] == "minor_error")
    major_error_count = sum(1 for r in field_results if r["status"] == "major_error")
    not_extracted_count = sum(
        1 for r in field_results if r["status"] == "not_extracted"
    )

    # Compute entity-level precision/recall/F1 (exact match)
    true_positives = exact_match_count
    false_positives = major_error_count + minor_error_count
    false_negatives = not_extracted_count
    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    # Compute average token-level F1
    token_f1_scores = [
        r.get("token_f1") for r in field_results if r.get("token_f1") is not None
    ]
    avg_token_f1 = (
        sum(token_f1_scores) / len(token_f1_scores) if token_f1_scores else None
    )

    result = {
        "field_results": field_results,
        "summary_stats": {
            "total_fields": total_fields,
            "extracted_count": extracted_count,
            "exact_match_count": exact_match_count,
            "minor_error_count": minor_error_count,
            "major_error_count": major_error_count,
            "not_extracted_count": not_extracted_count,
            "entity_precision": precision,
            "entity_recall": recall,
            "entity_f1": f1,
        },
    }

    if avg_token_f1 is not None:
        result["summary_stats"]["avg_token_f1"] = avg_token_f1

    return result
