"""Line item metrics plotting functions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


def plot_line_item_recall(
    stats: dict[str, Any],
    doc_type: str,
    output_path: Path,
) -> None:
    """Plot line-item recall vs number of items (GT list length).

    Args:
        stats: Statistics dictionary.
        doc_type: Document type (e.g., "deliverynote").
        output_path: Path to save the plot.
    """
    # Use raw stats if available (lists), otherwise use processed stats
    raw_line_item_metrics = stats.get("_raw_line_item_metrics", {})
    line_item_metrics = (
        raw_line_item_metrics.get(doc_type, {}) if raw_line_item_metrics else {}
    )

    if not line_item_metrics:
        return

    # Collect data: (gt_length, recall)
    data_points = []
    for _field_name, metrics_list in line_item_metrics.items():
        for metrics in metrics_list:
            gt_items = metrics.get("gt_items", 0)
            recall = metrics.get("items_recall", 0.0)
            if gt_items > 0:
                data_points.append((gt_items, recall))

    if not data_points:
        return

    # Bin by GT length
    bins = {}
    for gt_len, recall in data_points:
        # Round to nearest 5 for binning
        bin_key = (gt_len // 5) * 5
        if bin_key not in bins:
            bins[bin_key] = []
        bins[bin_key].append(recall)

    # Compute mean recall per bin
    bin_keys = sorted(bins.keys())
    bin_means = [np.mean(bins[k]) for k in bin_keys]
    bin_stds = [np.std(bins[k]) for k in bin_keys]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.errorbar(
        bin_keys,
        bin_means,
        yerr=bin_stds,
        marker="o",
        linestyle="-",
        linewidth=2,
        capsize=5,
        color="#2ecc71",
    )
    ax.set_xlabel("Number of Ground Truth Items (binned)")
    ax.set_ylabel("Mean Recall")
    ax.set_title(f"Line-Item Recall vs List Length - {doc_type.title()}")
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 1.1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
