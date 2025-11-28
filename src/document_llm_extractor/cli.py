"""Command-line interface for the document extraction pipeline.

This module provides the main CLI entry point for processing PDF documents
through the complete pipeline: OCR → LLM extraction → visualization.
"""

from .cli.main import main

__all__ = ["main"]
