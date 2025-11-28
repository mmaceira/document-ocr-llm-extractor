#!/usr/bin/env python3
"""Master script to generate all synthetic datasets.

This script calls all individual dataset generators:
- Bank statements
- Payroll / Payslips
- Albarán / Delivery notes

Each generator creates PDFs and JPGs (qualities 90, 40, 10) for ES, EN, and CA languages.

Usage:
    python tools/generate_dataset.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add tools directory to path so we can import the generators
TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))

from dataset_generators.deliverynote.generator import (  # noqa: E402
    main as generate_deliverynote,
)
from dataset_generators.generate_bank_dataset import main as generate_bank  # noqa: E402
from dataset_generators.payroll.main import main as generate_payroll  # noqa: E402


def main() -> None:
    """Generate all synthetic datasets."""
    print("=" * 70)
    print("Synthetic Dataset Generator - All Document Types")
    print("=" * 70)
    print()

    generators = [
        ("Bank Statements", generate_bank),
        ("Payroll / Payslips", generate_payroll),
        ("Delivery Notes", generate_deliverynote),
    ]

    for name, gen_func in generators:
        print(f"\n{'=' * 70}")
        print(f"Generating: {name}")
        print("=" * 70)
        try:
            gen_func()
        except Exception as e:
            print(f"\n[ERROR] Failed to generate {name}: {e}")
            print("Continuing with next dataset...\n")
            continue

    print("\n" + "=" * 70)
    print("All datasets generated successfully!")
    print("=" * 70)
    print("\nGenerated datasets:")
    print("  - data/bank/{pdf,images}/")
    print("  - data/payroll/{pdf,images}/")
    print("  - data/deliverynote/{pdf,images}/")
    print()


if __name__ == "__main__":
    main()
