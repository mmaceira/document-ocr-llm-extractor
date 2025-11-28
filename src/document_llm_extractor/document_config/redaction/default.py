"""Default redaction function."""

from __future__ import annotations

from ...core.visualizer import redact_sensitive_info


def default_redact(lines: list[str]) -> list[str]:
    """Default redaction using core.visualizer.redact_sensitive_info."""
    text = "\n".join(lines)
    text = redact_sensitive_info(text)
    return text.splitlines()
