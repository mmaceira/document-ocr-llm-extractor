"""Error analysis plotting functions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


def plot_error_pareto(
    stats: dict[str, Any],
    output_path: Path,
    top_n: int = 10,
) -> None:
    """Plot Pareto chart of error types.

    Args:
        stats: Statistics dictionary.
        output_path: Path to save the plot.
        top_n: Number of top error types to show.
    """
    error_types = stats.get("error_types", {})

    if not error_types:
        return

    # Sort by count
    sorted_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)
    sorted_errors = sorted_errors[:top_n]

    error_names = [e[0] for e in sorted_errors]
    error_counts = [e[1] for e in sorted_errors]
    cumulative = np.cumsum(error_counts) / sum(error_counts) * 100

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar chart
    ax1.bar(range(len(error_names)), error_counts, color="#e74c3c", alpha=0.7)
    ax1.set_xlabel("Error Type")
    ax1.set_ylabel("Count", color="#e74c3c")
    ax1.set_xticks(range(len(error_names)))
    ax1.set_xticklabels(error_names, rotation=45, ha="right")
    ax1.tick_params(axis="y", labelcolor="#e74c3c")
    ax1.grid(axis="y", alpha=0.3)

    # Cumulative line
    ax2 = ax1.twinx()
    ax2.plot(
        range(len(error_names)), cumulative, color="#3498db", marker="o", linewidth=2
    )
    ax2.set_ylabel("Cumulative %", color="#3498db")
    ax2.tick_params(axis="y", labelcolor="#3498db")
    ax2.set_ylim(0, 100)

    ax1.set_title(f"Error Type Pareto Chart (Top {top_n})")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
