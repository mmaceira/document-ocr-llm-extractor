#!/usr/bin/env python3
"""Table and line-item metrics (TEDS-lite).

This module provides functions to evaluate line-item extraction quality
by aligning rows and computing precision/recall/F1 at the item level.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from text_normalize import normalize_text


def align_rows(
    gt: list[dict], pr: list[dict], keys: tuple[str, ...]
) -> list[tuple[dict, dict]]:
    """Align ground truth and predicted rows by primary key(s).

    Uses greedy 1-1 matching based on concatenated key values.

    Args:
        gt: List of ground truth row dictionaries
        pr: List of predicted row dictionaries
        keys: Tuple of field names to use as primary key

    Returns:
        List of (gt_row, pr_row) pairs for matched rows
    """
    # Build map from normalized key to GT row
    gt_map = {}
    for g in gt:
        key = "||".join(normalize_text(str(g.get(k, ""))) for k in keys)
        if key:  # Only add non-empty keys
            gt_map[key] = g

    pairs = []
    used = set()

    for p in pr:
        key = "||".join(normalize_text(str(p.get(k, ""))) for k in keys)
        if key and key in gt_map and key not in used:
            pairs.append((gt_map[key], p))
            used.add(key)

    return pairs


def line_items_scores(
    gt_rows: list[dict],
    pr_rows: list[dict],
    keys: tuple[str, ...] = ("descripcion", "concepto", "producto"),
) -> dict:
    """Compute precision, recall, and F1 for line-item extraction.

    This is a lightweight approximation of TEDS/GriTS that focuses on
    item-level matching rather than full table structure.

    Args:
        gt_rows: List of ground truth line-item dictionaries
        pr_rows: List of predicted line-item dictionaries
        keys: Tuple of field names to use for matching rows

    Returns:
        Dictionary with items_precision, items_recall, items_f1
    """
    pairs = align_rows(gt_rows, pr_rows, keys)
    matched = len(pairs)

    recall_items = matched / max(1, len(gt_rows))
    precision_items = matched / max(1, len(pr_rows))

    f1 = (
        0.0
        if (precision_items + recall_items) == 0
        else 2 * precision_items * recall_items / (precision_items + recall_items)
    )

    return {
        "items_precision": precision_items,
        "items_recall": recall_items,
        "items_f1": f1,
        "matched_items": matched,
        "gt_items": len(gt_rows),
        "pr_items": len(pr_rows),
    }
