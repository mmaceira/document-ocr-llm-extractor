"""OCR metrics plotting functions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


def plot_ocr_histograms(
    stats: dict[str, Any],
    output_path: Path,
) -> None:
    """Plot OCR CER and WER distribution histograms.

    Args:
        stats: Statistics dictionary.
        output_path: Path to save the plot.
    """
    ocr_metrics = stats.get("ocr_metrics", {})
    cer_values = ocr_metrics.get("cer", [])
    wer_values = ocr_metrics.get("wer", [])

    if not cer_values and not wer_values:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    if cer_values:
        ax1.hist(cer_values, bins=30, color="#e74c3c", alpha=0.7, edgecolor="black")
        ax1.set_xlabel("Character Error Rate (CER)")
        ax1.set_ylabel("Frequency")
        ax1.set_title(f"CER Distribution (mean={np.mean(cer_values):.3f})")
        ax1.grid(axis="y", alpha=0.3)

    if wer_values:
        ax2.hist(wer_values, bins=30, color="#9b59b6", alpha=0.7, edgecolor="black")
        ax2.set_xlabel("Word Error Rate (WER)")
        ax2.set_ylabel("Frequency")
        ax2.set_title(f"WER Distribution (mean={np.mean(wer_values):.3f})")
        ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
