#!/usr/bin/env python3
"""Text normalization and token-level F1 scoring.

This module provides functions to normalize text (spaces, case, amounts, dates)
and compute token-level F1 scores for relaxed matching.
"""

from __future__ import annotations

import re
import unicodedata


def normalize_text(s: str) -> str:
    """Normalize text: Unicode normalization, whitespace cleanup.

    Args:
        s: Input string (can be None)

    Returns:
        Normalized string
    """
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.strip()
    return re.sub(r"\s+", " ", s)


def normalize_amount(s: str) -> str:
    """Normalize amount string: remove currency symbols, normalize separators.

    Handles European format (1.234,56) and converts to standard (1234.56).

    Args:
        s: Amount string (can be None)

    Returns:
        Normalized amount string (digits and decimal point only)
    """
    if s is None:
        return ""
    s = s.replace("€", "").replace("$", "").replace("£", "")
    # Handle European format: 1.234,56 -> 1234.56
    # Simple heuristic: if there are both . and , assume European format
    s = (
        s.replace(".", "").replace(",", ".")
        if "." in s and "," in s
        else s.replace(",", "")
    )
    return re.sub(r"[^\d\.\-]", "", s)


def normalize_date(s: str) -> str:
    """Normalize date string to ISO format (YYYY-MM-DD).

    Handles common formats: DD/MM/YYYY, YYYY-MM-DD, etc.

    Args:
        s: Date string (can be None)

    Returns:
        Normalized date string in ISO format, or original if parsing fails
    """
    if not s:
        return ""
    s = s.strip()
    # Extract all numeric parts
    mm = re.findall(r"(\d{1,4})", s)
    if len(mm) == 3:
        a, b, c = mm
        # Choose ordering by simple rule
        if len(a) == 4:
            # YYYY-MM-DD format
            return f"{a}-{int(b):02d}-{int(c):02d}"
        if len(c) == 4:
            # DD-MM-YYYY format
            return f"{c}-{int(b):02d}-{int(a):02d}"
        # Assume DD-MM-YY format, try to infer century
        year = f"20{int(c):02d}" if int(c) < 50 else f"19{int(c):02d}"
        return f"{year}-{int(b):02d}-{int(a):02d}"
    return s


def tokenize(s: str) -> list[str]:
    """Tokenize normalized text into words and numbers.

    Args:
        s: Input string

    Returns:
        List of tokens (words and numbers)
    """
    s = normalize_text(s.lower())
    return re.findall(r"[a-zA-Z0-9]+(?:\.[0-9]+)?", s)


def token_f1(pred: str, gt: str) -> tuple[float, float, float]:
    """Compute token-level precision, recall, and F1.

    This provides a relaxed matching metric that avoids over-penalizing
    minor string differences (whitespace, punctuation, case).

    Args:
        pred: Predicted string
        gt: Ground truth string

    Returns:
        Tuple of (precision, recall, f1)
    """
    ptoks, gtoks = set(tokenize(pred)), set(tokenize(gt))
    if not ptoks and not gtoks:
        return (1.0, 1.0, 1.0)
    if not ptoks:
        return (0.0, 0.0, 0.0)
    if not gtoks:
        return (0.0, 0.0, 0.0)
    tp = len(ptoks & gtoks)
    prec = tp / len(ptoks)
    rec = tp / len(gtoks)
    f1 = 0.0 if (prec + rec) == 0 else 2 * prec * rec / (prec + rec)
    return (prec, rec, f1)
