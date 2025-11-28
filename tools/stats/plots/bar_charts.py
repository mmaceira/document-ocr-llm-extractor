"""Bar chart plotting functions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


def plot_extraction_by_dimension(
    stats: dict[str, Any],
    dimension: str,
    title: str,
    output_path: Path,
) -> None:
    """Plot field extraction percentages by dimension.

    Args:
        stats: Statistics dictionary.
        dimension: Dimension key to plot (e.g., "by_doc_type").
        title: Plot title.
        output_path: Path to save the plot.
    """
    data = stats.get(dimension, {})

    categories = []
    exact_match = []
    minor_error = []
    major_error = []
    not_extracted = []

    for cat, info in data.items():
        if isinstance(info, dict) and "percentages" in info:
            percentages = info["percentages"]
            categories.append(cat)
            exact_match.append(percentages.get("exact_match", 0))
            minor_error.append(percentages.get("minor_error", 0))
            major_error.append(percentages.get("major_error", 0))
            not_extracted.append(percentages.get("not_extracted", 0))

    if not categories:
        return

    # Sort categories for quality dimension (low to high: 10, 40, 90, then pdf/unknown)
    # Also create descriptive labels for quality
    display_labels = categories.copy()
    if dimension == "by_quality":

        def quality_sort_key(cat: str) -> tuple[int, str]:
            """Sort quality: numeric values first (ascending), then non-numeric."""
            try:
                # Try to parse as integer (quality level)
                quality_num = int(cat)
                return (0, quality_num)  # Sort numeric values first
            except ValueError:
                # Non-numeric values (pdf, unknown, etc.) go last
                return (1, cat.lower())

        # Sort categories and corresponding data lists
        sorted_pairs = sorted(
            zip(
                categories,
                exact_match,
                minor_error,
                major_error,
                not_extracted,
                strict=False,
            ),
            key=lambda x: quality_sort_key(x[0]),
        )
        categories, exact_match, minor_error, major_error, not_extracted = zip(
            *sorted_pairs, strict=False
        )
        categories = list(categories)
        exact_match = list(exact_match)
        minor_error = list(minor_error)
        major_error = list(major_error)
        not_extracted = list(not_extracted)

        # Create descriptive labels for quality (after sorting)
        display_labels = []
        for cat in categories:
            cat_lower = cat.lower()
            if cat_lower == "pdf":
                display_labels.append("Best (PDF)")
            elif cat_lower in ("unknown", "none"):
                display_labels.append(f"Unknown ({cat})")
            else:
                try:
                    quality_num = int(cat)
                    if quality_num == 90:
                        display_labels.append("Good (JPG 90)")
                    elif quality_num == 40:
                        display_labels.append("Medium (JPG 40)")
                    elif quality_num == 10:
                        display_labels.append("Low (JPG 10)")
                    else:
                        display_labels.append(f"JPG {quality_num}")
                except ValueError:
                    display_labels.append(cat)

    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(categories))
    width = 0.6

    bottom2 = [exact_match[i] for i in range(len(categories))]
    bottom3 = [bottom2[i] + minor_error[i] for i in range(len(categories))]

    ax.bar(x, exact_match, width, label="Exact Match", color="#2ecc71")
    ax.bar(x, minor_error, width, bottom=bottom2, label="Minor Error", color="#f39c12")
    ax.bar(x, major_error, width, bottom=bottom3, label="Major Error", color="#e74c3c")
    ax.bar(
        x,
        not_extracted,
        width,
        bottom=[bottom3[i] + major_error[i] for i in range(len(categories))],
        label="Not Extracted",
        color="#95a5a6",
    )

    ax.set_xlabel(dimension.replace("_", " ").title())
    ax.set_ylabel("Percentage (%)")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(display_labels, rotation=45, ha="right")
    ax.legend()
    ax.set_ylim(0, 100)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
