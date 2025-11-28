#!/usr/bin/env python3
"""Generate statistics and plots from evaluation results.

This script aggregates evaluation metrics and generates JSON statistics and plots.

Usage:
    python -m tools.stats.main --evaluations-dir evaluations --statistics-dir statistics
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import seaborn as sns

from .aggregator import aggregate_statistics, calculate_percentages
from .loader import load_evaluations
from .plots.bar_charts import plot_extraction_by_dimension
from .plots.error_plots import plot_error_pareto
from .plots.field_plots import plot_per_field_accuracy, plot_per_field_f1_with_ci
from .plots.heatmaps import plot_heatmap
from .plots.line_item_plots import plot_line_item_recall
from .plots.ocr_plots import plot_ocr_histograms

# Set style
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)


def main() -> None:
    """Main entry point for statistics generation."""
    parser = argparse.ArgumentParser(
        description="Generate statistics and plots from evaluations"
    )
    parser.add_argument(
        "--outputs-dir",
        type=Path,
        default=Path("outputs"),
        help="Base output directory (should contain '{ocr-engine}/evaluations' subdirectory)",
    )
    parser.add_argument(
        "--ocr-engine",
        type=str,
        default="rapidocr",
        choices=["rapidocr", "tesseract", "docling"],
        help="OCR engine used for inference (default: rapidocr)",
    )
    parser.add_argument(
        "--evaluations-dir",
        type=Path,
        default=None,
        help=(
            "Directory containing evaluation results "
            "(default: {outputs-dir}/{ocr-engine}/evaluations)"
        ),
    )
    parser.add_argument(
        "--statistics-dir",
        type=Path,
        default=None,
        help=(
            "Directory to save statistics and plots "
            "(default: {outputs-dir}/{ocr-engine}/statistics)"
        ),
    )
    args = parser.parse_args()

    outputs_dir = args.outputs_dir
    # Evaluations and statistics go to outputs/{ocr_engine}/evaluations
    # and outputs/{ocr_engine}/statistics
    evaluations_dir = args.evaluations_dir or (
        outputs_dir / args.ocr_engine / "evaluations"
    )
    statistics_dir = args.statistics_dir or (
        outputs_dir / args.ocr_engine / "statistics"
    )
    statistics_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = statistics_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Statistics Generation")
    print("=" * 70)
    print(f"Base outputs directory: {outputs_dir}")
    print(f"Evaluations directory: {evaluations_dir}")
    print(f"Statistics directory: {statistics_dir}")
    print()

    # Load evaluations
    print("Loading evaluations...")
    evaluations = load_evaluations(evaluations_dir)
    print(f"Loaded {len(evaluations)} evaluations")

    # Aggregate statistics
    print("Aggregating statistics...")
    raw_stats = aggregate_statistics(evaluations)
    stats = calculate_percentages(raw_stats)

    # Keep raw stats for plotting functions that need lists
    stats["_raw_per_field_token_f1"] = raw_stats.get("per_field_token_f1", {})
    stats["_raw_line_item_metrics"] = raw_stats.get("line_item_metrics", {})

    # Save JSON statistics
    stats_file = statistics_dir / "field_extraction_stats.json"

    # Convert defaultdict to regular dict for JSON serialization
    def convert_defaultdict(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: convert_defaultdict(v) for k, v in obj.items()}
        return obj

    json_stats = convert_defaultdict(stats)
    stats_file.write_text(
        json.dumps(json_stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved statistics to {stats_file}")

    # Generate plots
    print("Generating plots...")
    print()

    # Bar charts by dimension
    print("  → extraction_by_doc_type.png")
    plot_extraction_by_dimension(
        stats,
        "by_doc_type",
        "Field Extraction % by Document Type",
        plots_dir / "extraction_by_doc_type.png",
    )

    print("  → extraction_by_language.png")
    plot_extraction_by_dimension(
        stats,
        "by_language",
        "Field Extraction % by Language",
        plots_dir / "extraction_by_language.png",
    )

    print("  → extraction_by_quality.png")
    plot_extraction_by_dimension(
        stats,
        "by_quality",
        "Field Extraction % by Quality",
        plots_dir / "extraction_by_quality.png",
    )

    print("  → extraction_by_file_type.png")
    plot_extraction_by_dimension(
        stats,
        "by_file_type",
        "Field Extraction % by File Type",
        plots_dir / "extraction_by_file_type.png",
    )

    # Heatmaps
    print("  → heatmap_doc_type_quality.png")
    plot_heatmap(
        stats,
        "by_doc_type_quality",
        "Field Extraction % by Document Type × Quality",
        plots_dir / "heatmap_doc_type_quality.png",
    )

    print("  → heatmap_doc_type_language.png")
    plot_heatmap(
        stats,
        "by_doc_type_language",
        "Field Extraction % by Document Type × Language",
        plots_dir / "heatmap_doc_type_language.png",
    )

    # Get configured document types
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from document_llm_extractor.document_config import DOCUMENT_CONFIGS

    # Per-field accuracy
    for doc_type in DOCUMENT_CONFIGS:
        print(f"  → per_field_accuracy_{doc_type}.png")
        plot_per_field_accuracy(
            stats,
            doc_type,
            plots_dir / f"per_field_accuracy_{doc_type}.png",
        )

        print(f"  → per_field_f1_ci_{doc_type}.png")
        # Per-field F1 with CIs
        plot_per_field_f1_with_ci(
            stats,
            doc_type,
            plots_dir / f"per_field_f1_ci_{doc_type}.png",
        )

        print(f"  → line_item_recall_{doc_type}.png")
        # Line-item recall vs list length
        plot_line_item_recall(
            stats,
            doc_type,
            plots_dir / f"line_item_recall_{doc_type}.png",
        )

    # OCR histograms
    print("  → ocr_histograms.png")
    plot_ocr_histograms(
        stats,
        plots_dir / "ocr_histograms.png",
    )

    # Error Pareto chart
    print("  → error_pareto.png")
    plot_error_pareto(
        stats,
        plots_dir / "error_pareto.png",
        top_n=10,
    )

    plot_count = len(list(plots_dir.glob("*.png")))
    print(f"\nGenerated {plot_count} plots in {plots_dir}")
    print("\nFor detailed explanations of each graph, see: docs/STATISTICS_GRAPHS.md")
    print()
    print("=" * 70)
    print("Statistics generation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
