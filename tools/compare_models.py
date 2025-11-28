#!/usr/bin/env python3
"""Model comparison using McNemar's test.

This script compares two model variants on the same documents using
McNemar's test for paired comparisons, which is appropriate when
evaluating the same documents with different models.
"""

from __future__ import annotations

import argparse
import json
from math import comb, pow
from pathlib import Path
from typing import Any


def mcnemar(b: int, c: int) -> tuple[float, float]:
    """Compute McNemar's test statistic and p-value.

    Tests the null hypothesis that two models have equal performance
    on paired data. b = A correct, B wrong; c = A wrong, B correct.

    Args:
        b: Number of cases where model A is correct and model B is wrong
        c: Number of cases where model A is wrong and model B is correct

    Returns:
        Tuple of (test_statistic, p_value)
    """
    n = b + c
    if n == 0:
        return (0.0, 1.0)

    # Two-sided exact binomial p-value under H0: p=0.5
    k = min(b, c)
    p = 0.0
    for i in range(0, k + 1):
        p += comb(n, i) * pow(0.5, n)
    p *= 2.0

    # Edwards' continuity corrected statistic
    stat = (abs(b - c) - 1) ** 2 / n if n > 0 else 0.0

    return (stat, min(1.0, p))


def load_eval(path: Path) -> dict[str, Any]:
    """Load evaluation JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def main(dir_A: str, dir_B: str, field: str) -> None:
    """Compare two evaluation directories for a specific field.

    Args:
        dir_A: Path to first evaluation directory
        dir_B: Path to second evaluation directory
        field: Field name to compare
    """
    A_files = {p.name: p for p in Path(dir_A).glob("*.json")}
    B_files = {p.name: p for p in Path(dir_B).glob("*.json")}
    common = sorted(set(A_files) & set(B_files))

    if not common:
        print(f"[ERROR] No common files found between {dir_A} and {dir_B}")
        return

    b = c = 0
    total = 0

    for name in common:
        try:
            A = load_eval(A_files[name])
            B = load_eval(B_files[name])

            # Find the field result
            a_ok = False
            b_ok = False

            field_results_A = A.get("field_results", [])
            field_results_B = B.get("field_results", [])

            for fr in field_results_A:
                if fr.get("field_name") == field:
                    a_ok = fr.get("status") == "exact_match"
                    break

            for fr in field_results_B:
                if fr.get("field_name") == field:
                    b_ok = fr.get("status") == "exact_match"
                    break

            total += 1
            if a_ok and not b_ok:
                b += 1
            elif b_ok and not a_ok:
                c += 1
        except Exception as e:
            print(f"[WARNING] Failed to process {name}: {e}")
            continue

    if total == 0:
        print(f"[ERROR] No valid comparisons found for field '{field}'")
        return

    stat, p = mcnemar(b, c)

    print("=" * 70)
    print(f"McNemar's Test for field: {field}")
    print("=" * 70)
    print(f"Total documents compared: {total}")
    print(f"Model A correct, Model B wrong: {b}")
    print(f"Model A wrong, Model B correct: {c}")
    print(f"Test statistic: {stat:.3f}")
    print(f"P-value: {p:.4g}")
    if p < 0.05:
        print("Result: Significant difference (p < 0.05)")
    else:
        print("Result: No significant difference (p >= 0.05)")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare two model evaluations using McNemar's test"
    )
    parser.add_argument(
        "--eval-dir-A",
        required=True,
        help="Path to first evaluation directory",
    )
    parser.add_argument(
        "--eval-dir-B",
        required=True,
        help="Path to second evaluation directory",
    )
    parser.add_argument(
        "--field",
        required=True,
        help="Field name to compare",
    )
    args = parser.parse_args()

    main(args.eval_dir_A, args.eval_dir_B, args.field)
