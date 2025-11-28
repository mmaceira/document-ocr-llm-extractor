"""Load evaluation results from files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_evaluations(evaluations_dir: Path) -> list[dict[str, Any]]:
    """Load all evaluation results.

    Args:
        evaluations_dir: Directory containing evaluation JSON files.

    Returns:
        List of evaluation dictionaries.
    """
    evaluations = []

    for doc_type_dir in evaluations_dir.iterdir():
        if not doc_type_dir.is_dir():
            continue

        doc_type = doc_type_dir.name
        if doc_type not in {"deliverynote", "bank", "id", "payroll"}:
            continue

        for lang_dir in doc_type_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            for eval_file in lang_dir.glob("*_evaluation.json"):
                try:
                    eval_data = json.loads(eval_file.read_text(encoding="utf-8"))
                    evaluations.append(eval_data)
                except Exception as e:
                    print(f"[WARNING] Failed to load {eval_file}: {e}")

    return evaluations
