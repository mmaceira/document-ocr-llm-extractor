"""Aggregate statistics from evaluation results."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from bootstrap import bootstrap_ci


def aggregate_statistics(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate statistics from evaluations.

    Args:
        evaluations: List of evaluation dictionaries.

    Returns:
        Dictionary with aggregated statistics.
    """
    stats = {
        "by_doc_type": defaultdict(lambda: defaultdict(int)),
        "by_language": defaultdict(lambda: defaultdict(int)),
        "by_quality": defaultdict(lambda: defaultdict(int)),
        "by_file_type": defaultdict(lambda: defaultdict(int)),
        "by_doc_type_quality": defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        ),
        "by_doc_type_language": defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        ),
        "per_field": defaultdict(lambda: defaultdict(lambda: defaultdict(int))),
        "per_field_token_f1": defaultdict(lambda: defaultdict(list)),
        "per_field_entity_f1": defaultdict(lambda: defaultdict(list)),
        "ocr_metrics": {"cer": [], "wer": []},
        "line_item_metrics": defaultdict(lambda: defaultdict(list)),
        "error_types": defaultdict(int),
    }

    for eval_data in evaluations:
        metadata = eval_data.get("metadata", {})
        summary = eval_data.get("summary_stats", {})
        field_results = eval_data.get("field_results", [])

        doc_type = metadata.get("doc_type", "unknown")
        lang = metadata.get("lang", "unknown")
        quality = metadata.get("quality", "unknown")
        file_type = metadata.get("file_type", "unknown")

        # Aggregate by dimensions - accumulate counts
        total_fields = summary.get("total_fields", 0)
        if total_fields > 0:
            stats["by_doc_type"][doc_type]["total_fields"] += total_fields
            stats["by_language"][lang]["total_fields"] += total_fields
            stats["by_quality"][quality]["total_fields"] += total_fields
            stats["by_file_type"][file_type]["total_fields"] += total_fields
            stats["by_doc_type_quality"][doc_type][quality][
                "total_fields"
            ] += total_fields
            stats["by_doc_type_language"][doc_type][lang][
                "total_fields"
            ] += total_fields

        for key in [
            "extracted_count",
            "exact_match_count",
            "minor_error_count",
            "major_error_count",
            "not_extracted_count",
        ]:
            count = summary.get(key, 0)
            stats["by_doc_type"][doc_type][key] += count
            stats["by_language"][lang][key] += count
            stats["by_quality"][quality][key] += count
            stats["by_file_type"][file_type][key] += count
            stats["by_doc_type_quality"][doc_type][quality][key] += count
            stats["by_doc_type_language"][doc_type][lang][key] += count

        # Per-field statistics
        for field_result in field_results:
            field_name = field_result.get("field_name", "unknown")
            status = field_result.get("status", "unknown")
            stats["per_field"][doc_type][field_name][status] += 1

            # Collect token F1 scores
            token_f1 = field_result.get("token_f1")
            if token_f1 is not None:
                stats["per_field_token_f1"][doc_type][field_name].append(token_f1)

            # Collect error type categories
            error_type_cat = field_result.get("error_type_category", "unknown")
            stats["error_types"][error_type_cat] += 1

            # Collect line-item metrics
            line_item_metrics = field_result.get("line_item_metrics")
            if line_item_metrics:
                stats["line_item_metrics"][doc_type][field_name].append(
                    line_item_metrics
                )

        # Collect entity-level F1
        entity_f1 = summary.get("entity_f1")
        if entity_f1 is not None:
            stats["per_field_entity_f1"][doc_type]["overall"].append(entity_f1)

        # Collect OCR metrics
        ocr_metrics = eval_data.get("ocr", {})
        if ocr_metrics:
            if "cer" in ocr_metrics:
                stats["ocr_metrics"]["cer"].append(ocr_metrics["cer"])
            if "wer" in ocr_metrics:
                stats["ocr_metrics"]["wer"].append(ocr_metrics["wer"])

    return stats


def calculate_percentages(stats: dict[str, Any]) -> dict[str, Any]:
    """Calculate percentages from counts and add bootstrap CIs for metrics.

    Args:
        stats: Raw aggregated statistics.

    Returns:
        Dictionary with percentages and confidence intervals added.
    """
    result = {}

    # Add bootstrap CIs for per-field token F1
    if "per_field_token_f1" in stats:
        result["per_field_token_f1"] = {}
        for doc_type, fields in stats["per_field_token_f1"].items():
            result["per_field_token_f1"][doc_type] = {}
            for field_name, f1_values in fields.items():
                if f1_values:
                    mean, low, high = bootstrap_ci(f1_values)
                    result["per_field_token_f1"][doc_type][field_name] = {
                        "mean": mean,
                        "ci_low": low,
                        "ci_high": high,
                        "n": len(f1_values),
                    }

    # Add bootstrap CIs for entity-level F1
    if "per_field_entity_f1" in stats:
        result["per_field_entity_f1"] = {}
        for doc_type, fields in stats["per_field_entity_f1"].items():
            result["per_field_entity_f1"][doc_type] = {}
            for field_name, f1_values in fields.items():
                if f1_values:
                    mean, low, high = bootstrap_ci(f1_values)
                    result["per_field_entity_f1"][doc_type][field_name] = {
                        "mean": mean,
                        "ci_low": low,
                        "ci_high": high,
                        "n": len(f1_values),
                    }

    # Add OCR metrics with CIs
    if "ocr_metrics" in stats:
        result["ocr_metrics"] = {}
        for metric_name, values in stats["ocr_metrics"].items():
            if values:
                mean, low, high = bootstrap_ci(values)
                result["ocr_metrics"][metric_name] = {
                    "mean": mean,
                    "ci_low": low,
                    "ci_high": high,
                    "n": len(values),
                }

    # Add line-item metrics summary
    if "line_item_metrics" in stats:
        result["line_item_metrics"] = {}
        for doc_type, fields in stats["line_item_metrics"].items():
            result["line_item_metrics"][doc_type] = {}
            for field_name, metrics_list in fields.items():
                if metrics_list:
                    recalls = [m.get("items_recall", 0.0) for m in metrics_list]
                    precisions = [m.get("items_precision", 0.0) for m in metrics_list]
                    f1s = [m.get("items_f1", 0.0) for m in metrics_list]

                    if recalls:
                        rec_mean, rec_low, rec_high = bootstrap_ci(recalls)
                        prec_mean, prec_low, prec_high = bootstrap_ci(precisions)
                        f1_mean, f1_low, f1_high = bootstrap_ci(f1s)

                        result["line_item_metrics"][doc_type][field_name] = {
                            "recall": {
                                "mean": rec_mean,
                                "ci_low": rec_low,
                                "ci_high": rec_high,
                            },
                            "precision": {
                                "mean": prec_mean,
                                "ci_low": prec_low,
                                "ci_high": prec_high,
                            },
                            "f1": {
                                "mean": f1_mean,
                                "ci_low": f1_low,
                                "ci_high": f1_high,
                            },
                            "n": len(metrics_list),
                        }

    # Add error types summary
    if "error_types" in stats:
        result["error_types"] = dict(stats["error_types"])

    # Calculate percentages for each aggregation
    # Skip keys that are already processed above
    skip_keys = {
        "per_field_token_f1",
        "per_field_entity_f1",
        "ocr_metrics",
        "line_item_metrics",
        "error_types",
    }

    for key, data in stats.items():
        # Skip keys already processed
        if key in skip_keys:
            continue

        if key == "per_field":
            # Handle per-field separately
            result[key] = {}
            for doc_type, fields in data.items():
                result[key][doc_type] = {}
                for field_name, status_counts in fields.items():
                    total = sum(status_counts.values())
                    if total > 0:
                        result[key][doc_type][field_name] = {
                            status: (count / total * 100, count)
                            for status, count in status_counts.items()
                        }
                    else:
                        result[key][doc_type][field_name] = {}
            continue

        # Skip if data is not a dict (e.g., lists or other types)
        if not isinstance(data, dict):
            continue

        result[key] = {}
        for dimension, counts in data.items():
            if isinstance(counts, dict):
                total = counts.get("total_fields", 0)
                if total == 0:
                    # Fallback: use sum of all status counts
                    total = sum(
                        counts.get(k, 0)
                        for k in [
                            "exact_match_count",
                            "minor_error_count",
                            "major_error_count",
                            "not_extracted_count",
                        ]
                    )
                if total == 0:
                    total = 1  # Avoid division by zero

                result[key][dimension] = {
                    "counts": counts,
                    "percentages": {
                        "extracted": (
                            (counts.get("extracted_count", 0) / total * 100)
                            if total > 0
                            else 0
                        ),
                        "exact_match": (
                            (counts.get("exact_match_count", 0) / total * 100)
                            if total > 0
                            else 0
                        ),
                        "minor_error": (
                            (counts.get("minor_error_count", 0) / total * 100)
                            if total > 0
                            else 0
                        ),
                        "major_error": (
                            (counts.get("major_error_count", 0) / total * 100)
                            if total > 0
                            else 0
                        ),
                        "not_extracted": (
                            (counts.get("not_extracted_count", 0) / total * 100)
                            if total > 0
                            else 0
                        ),
                    },
                }
            else:
                # Nested structure (doc_type_quality, doc_type_language)
                result[key][dimension] = {}
                for sub_dimension, sub_counts in counts.items():
                    total = sub_counts.get("total_fields", 0)
                    if total == 0:
                        # Fallback: use sum of all status counts
                        total = sum(
                            sub_counts.get(k, 0)
                            for k in [
                                "exact_match_count",
                                "minor_error_count",
                                "major_error_count",
                                "not_extracted_count",
                            ]
                        )
                    if total == 0:
                        total = 1  # Avoid division by zero

                    result[key][dimension][sub_dimension] = {
                        "counts": sub_counts,
                        "percentages": {
                            "extracted": (
                                (sub_counts.get("extracted_count", 0) / total * 100)
                                if total > 0
                                else 0
                            ),
                            "exact_match": (
                                (sub_counts.get("exact_match_count", 0) / total * 100)
                                if total > 0
                                else 0
                            ),
                            "minor_error": (
                                (sub_counts.get("minor_error_count", 0) / total * 100)
                                if total > 0
                                else 0
                            ),
                            "major_error": (
                                (sub_counts.get("major_error_count", 0) / total * 100)
                                if total > 0
                                else 0
                            ),
                            "not_extracted": (
                                (sub_counts.get("not_extracted_count", 0) / total * 100)
                                if total > 0
                                else 0
                            ),
                        },
                    }

    return result
