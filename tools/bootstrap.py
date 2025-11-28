#!/usr/bin/env python3
"""Bootstrap confidence intervals for metrics.

This module provides functions to compute bootstrap confidence intervals
for any metric, allowing uncertainty quantification in evaluation results.
"""

from __future__ import annotations

import random


def bootstrap_ci(
    values: list[float], B: int = 2000, alpha: float = 0.05
) -> tuple[float, float, float]:
    """Compute bootstrap confidence interval for a list of values.

    Uses percentile method to compute (1-alpha)*100% confidence interval.

    Args:
        values: List of metric values (one per document/example)
        B: Number of bootstrap samples (default: 2000)
        alpha: Significance level (default: 0.05 for 95% CI)

    Returns:
        Tuple of (mean, lower_bound, upper_bound)
    """
    if not values:
        return (float("nan"), float("nan"), float("nan"))

    n = len(values)
    boots = []

    for _ in range(B):
        sample = [values[random.randrange(n)] for _ in range(n)]
        boots.append(sum(sample) / n)

    boots.sort()
    lo_idx = int((alpha / 2) * B)
    hi_idx = int((1 - alpha / 2) * B)
    # Clamp indices to valid range
    lo_idx = max(0, min(lo_idx, len(boots) - 1))
    hi_idx = max(0, min(hi_idx, len(boots) - 1))

    lo = boots[lo_idx]
    hi = boots[hi_idx]
    mean = sum(values) / n

    return (mean, lo, hi)
