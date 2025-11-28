#!/usr/bin/env python3
"""OCR quality metrics: Character Error Rate (CER) and Word Error Rate (WER).

This module provides functions to compute CER and WER between reference and
hypothesis text, which are standard metrics for OCR quality evaluation.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass


def _levenshtein(a: list[str], b: list[str]) -> int:
    """Compute Levenshtein distance between two sequences."""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[m][n]


def cer(ref: str, hyp: str) -> float:
    """Compute Character Error Rate (CER) between reference and hypothesis.

    CER = (number of character errors) / (number of reference characters)

    Args:
        ref: Reference text (ground truth)
        hyp: Hypothesis text (OCR output)

    Returns:
        CER value between 0.0 (perfect match) and 1.0+ (errors)
    """
    if not ref:
        return 0.0 if not hyp else 1.0
    dist = _levenshtein(list(ref), list(hyp))
    return dist / len(ref)


def wer(ref: str, hyp: str) -> float:
    """Compute Word Error Rate (WER) between reference and hypothesis.

    WER = (number of word errors) / (number of reference words)

    Args:
        ref: Reference text (ground truth)
        hyp: Hypothesis text (OCR output)

    Returns:
        WER value between 0.0 (perfect match) and 1.0+ (errors)
    """
    ref_words = ref.split()
    hyp_words = hyp.split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    dist = _levenshtein(ref_words, hyp_words)
    return dist / len(ref_words)


@dataclass
class OcrScores:
    """OCR quality scores."""

    cer: float
    wer: float


def score_ocr(
    reference_texts: Iterable[str], hypothesis_texts: Iterable[str]
) -> OcrScores:
    """Compute average CER and WER over multiple text pairs.

    Args:
        reference_texts: Iterable of reference (ground truth) texts
        hypothesis_texts: Iterable of hypothesis (OCR output) texts

    Returns:
        OcrScores with mean CER and WER

    Raises:
        AssertionError: If the lengths of the two iterables don't match
    """
    refs, hyps = list(reference_texts), list(hypothesis_texts)
    assert len(refs) == len(hyps), "Mismatched lengths"
    cer_vals, wer_vals = [], []
    for r, h in zip(refs, hyps, strict=False):
        cer_vals.append(cer(r, h))
        wer_vals.append(wer(r, h))

    def mean(xs):
        return sum(xs) / len(xs) if xs else math.nan

    return OcrScores(cer=mean(cer_vals), wer=mean(wer_vals))
