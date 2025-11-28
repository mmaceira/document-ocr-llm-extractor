"""Heatmap plotting functions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import seaborn as sns


def plot_heatmap(
    stats: dict[str, Any],
    dimension: str,
    title: str,
    output_path: Path,
) -> None:
    """Plot heatmap for two-dimensional aggregation.

    Args:
        stats: Statistics dictionary.
        dimension: Dimension key to plot (e.g., "by_doc_type_quality").
        title: Plot title.
        output_path: Path to save the plot.
    """
    data = stats.get(dimension, {})

    # Build matrix
    rows = []
    cols = []
    values = []

    for key1, sub_data in data.items():
        if isinstance(sub_data, dict):
            for key2, info in sub_data.items():
                if isinstance(info, dict) and "percentages" in info:
                    rows.append(key1)
                    cols.append(key2)
                    percentages = info["percentages"]
                    # Use exact_match percentage for heatmap
                    values.append(percentages.get("exact_match", 0))

    if not rows:
        return

    # Create DataFrame-like structure
    unique_rows = sorted(set(rows))
    unique_cols = sorted(set(cols))

    matrix = []
    for row in unique_rows:
        row_data = []
        for col in unique_cols:
            # Find matching value
            value = 0
            for _i, (r, c, v) in enumerate(zip(rows, cols, values, strict=False)):
                if r == row and c == col:
                    value = v
                    break
            row_data.append(value)
        matrix.append(row_data)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(
        matrix,
        xticklabels=unique_cols,
        yticklabels=unique_rows,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        cbar_kws={"label": "Exact Match %"},
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel(dimension.split("_")[-1].title())
    ax.set_ylabel(dimension.split("_")[0].title())

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
