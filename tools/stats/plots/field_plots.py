"""Per-field plotting functions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from bootstrap import bootstrap_ci


def plot_per_field_accuracy(
    stats: dict[str, Any],
    doc_type: str,
    output_path: Path,
) -> None:
    """Plot per-field accuracy for a document type.

    Args:
        stats: Statistics dictionary.
        doc_type: Document type (e.g., "deliverynote").
        output_path: Path to save the plot.
    """
    per_field = stats.get("per_field", {}).get(doc_type, {})

    if not per_field:
        return

    fields = []
    exact_match = []
    minor_error = []
    major_error = []
    not_extracted = []

    for field_name, field_stats in per_field.items():
        if isinstance(field_stats, dict):
            fields.append(field_name)
            exact_match.append(field_stats.get("exact_match", (0, 0))[0])
            minor_error.append(field_stats.get("minor_error", (0, 0))[0])
            major_error.append(field_stats.get("major_error", (0, 0))[0])
            not_extracted.append(field_stats.get("not_extracted", (0, 0))[0])

    if not fields:
        return

    fig, ax = plt.subplots(figsize=(14, 8))
    x = range(len(fields))
    width = 0.6

    bottom2 = [exact_match[i] for i in range(len(fields))]
    bottom3 = [bottom2[i] + minor_error[i] for i in range(len(fields))]

    ax.bar(x, exact_match, width, label="Exact Match", color="#2ecc71")
    ax.bar(x, minor_error, width, bottom=bottom2, label="Minor Error", color="#f39c12")
    ax.bar(x, major_error, width, bottom=bottom3, label="Major Error", color="#e74c3c")
    ax.bar(
        x,
        not_extracted,
        width,
        bottom=[bottom3[i] + major_error[i] for i in range(len(fields))],
        label="Not Extracted",
        color="#95a5a6",
    )

    ax.set_xlabel("Field Name")
    ax.set_ylabel("Percentage (%)")
    ax.set_title(f"Field Extraction Accuracy - {doc_type.title()}")
    ax.set_xticks(x)
    ax.set_xticklabels(fields, rotation=45, ha="right")
    ax.legend()
    ax.set_ylim(0, 100)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_per_field_f1_with_ci(
    stats: dict[str, Any],
    doc_type: str,
    output_path: Path,
) -> None:
    """Plot per-field F1 scores with 95% confidence intervals.

    Args:
        stats: Statistics dictionary.
        doc_type: Document type (e.g., "deliverynote").
        output_path: Path to save the plot.
    """
    # Use raw stats if available (lists), otherwise use processed stats (dicts with CIs)
    raw_per_field_f1 = stats.get("_raw_per_field_token_f1", {})
    if raw_per_field_f1:
        per_field_f1 = raw_per_field_f1.get(doc_type, {})
    else:
        # Fallback to processed stats - but they're dicts, not lists
        # This shouldn't happen, but handle gracefully
        processed_f1 = stats.get("per_field_token_f1", {}).get(doc_type, {})
        if processed_f1 and isinstance(next(iter(processed_f1.values()), None), dict):
            # Processed format - extract means for plotting (no CIs in this case)
            per_field_f1 = {
                field: [v.get("mean", 0.0)] for field, v in processed_f1.items()
            }
        else:
            per_field_f1 = processed_f1

    if not per_field_f1:
        return

    fields = []
    f1_means = []
    f1_lows = []
    f1_highs = []

    for field_name, f1_values in per_field_f1.items():
        if not f1_values:
            continue
        fields.append(field_name)
        mean, low, high = bootstrap_ci(f1_values)
        f1_means.append(mean)
        f1_lows.append(low)
        f1_highs.append(high)

    if not fields:
        return

    fig, ax = plt.subplots(figsize=(14, 8))
    x = range(len(fields))
    width = 0.6

    # Plot bars with error bars
    errors_low = [f1_means[i] - f1_lows[i] for i in range(len(f1_means))]
    errors_high = [f1_highs[i] - f1_means[i] for i in range(len(f1_means))]
    ax.bar(
        x,
        f1_means,
        width,
        yerr=[errors_low, errors_high],
        capsize=5,
        color="#3498db",
        alpha=0.7,
    )

    ax.set_xlabel("Field Name")
    ax.set_ylabel("Token-level F1 Score")
    ax.set_title(f"Per-Field Token F1 with 95% CI - {doc_type.title()}")
    ax.set_xticks(x)
    ax.set_xticklabels(fields, rotation=45, ha="right")
    ax.set_ylim(0, 1.1)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
