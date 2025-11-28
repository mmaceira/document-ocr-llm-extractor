#!/usr/bin/env python3
"""Evaluate extracted results against ground truth.

This script compares extracted fields against ground truth and classifies errors.

Usage:
    python -m tools.evaluation.main --outputs-dir outputs
        --ground-truth-dir data --evaluations-dir evaluations
"""

from __future__ import annotations

import argparse
import json

# Import OCR metrics
import sys
from pathlib import Path

from .document_evaluator import evaluate_document

sys.path.insert(0, str(Path(__file__).parent.parent))
from ocr_metrics import cer, wer

# Import document config to get available document types
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from document_llm_extractor.document_config import DOCUMENT_CONFIGS


def main() -> None:
    """Main entry point for evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate extracted results against ground truth"
    )
    parser.add_argument(
        "--outputs-dir",
        type=Path,
        default=Path("outputs"),
        help="Base output directory (should contain '{ocr-engine}/inference' subdirectory)",
    )
    parser.add_argument(
        "--ocr-engine",
        type=str,
        default="rapidocr",
        choices=["rapidocr", "tesseract", "docling"],
        help="OCR engine used for inference (default: rapidocr)",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing ground truth files",
    )
    parser.add_argument(
        "--evaluations-dir",
        type=Path,
        default=None,
        help="Directory to save evaluation results (default: {outputs-dir}/evaluations)",
    )
    args = parser.parse_args()

    outputs_dir = args.outputs_dir
    ground_truth_dir = args.ground_truth_dir
    # Evaluations go to outputs/{ocr_engine}/evaluations
    evaluations_dir = args.evaluations_dir or (
        outputs_dir / args.ocr_engine / "evaluations"
    )
    evaluations_dir.mkdir(parents=True, exist_ok=True)

    # Look for inference results in outputs/{ocr_engine}/inference
    inference_dir = outputs_dir / args.ocr_engine / "inference"

    print("=" * 70)
    print("Evaluation Pipeline")
    print("=" * 70)
    print(f"Base outputs directory: {outputs_dir}")
    print(f"Inference directory: {inference_dir}")
    print(f"Ground truth directory: {ground_truth_dir}")
    print(f"Evaluations directory: {evaluations_dir}")
    print()

    total_evaluated = 0
    total_failed = 0

    # Find all inference results
    if not inference_dir.exists():
        print(f"[ERROR] Inference directory not found: {inference_dir}")
        print("       Make sure to run batch_inference.py first")
        return

    for doc_type_dir in inference_dir.iterdir():
        if not doc_type_dir.is_dir():
            continue

        doc_type = doc_type_dir.name
        # Only process document types that are configured
        if doc_type not in DOCUMENT_CONFIGS:
            continue

        for lang_dir in doc_type_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            lang = lang_dir.name
            eval_lang_dir = evaluations_dir / doc_type / lang
            eval_lang_dir.mkdir(parents=True, exist_ok=True)

            # Process all JSON files
            for result_file in lang_dir.glob("*.json"):
                if result_file.name.endswith("_viz.json"):
                    continue

                total_evaluated += 1
                base_name = result_file.stem

                # Load inference result
                try:
                    result_data = json.loads(result_file.read_text(encoding="utf-8"))
                except Exception as e:
                    print(f"[ERROR] Failed to load {result_file}: {e}")
                    total_failed += 1
                    continue

                extracted_data = result_data.get("extracted_data", {})

                # Find corresponding ground truth
                # Ground truth filename format: {base_name}_ground_truth.json
                # But base_name might have _p1_q90 suffix for images or _q90 for quality
                gt_base_name = base_name
                # Strip page suffix (_p1, _p2, etc.)
                if "_p" in gt_base_name:
                    gt_base_name = gt_base_name.split("_p")[0]
                # Strip quality suffix (_q10, _q40, _q90, etc.)
                if "_q" in gt_base_name:
                    gt_base_name = gt_base_name.split("_q")[0]

                gt_file = (
                    ground_truth_dir
                    / doc_type
                    / "ground_truth"
                    / lang
                    / f"{gt_base_name}_ground_truth.json"
                )

                if not gt_file.exists():
                    print(f"[WARNING] Ground truth not found for {result_file.name}")
                    total_failed += 1
                    continue

                # Load ground truth
                try:
                    ground_truth_data = json.loads(gt_file.read_text(encoding="utf-8"))
                except Exception as e:
                    print(f"[ERROR] Failed to load ground truth {gt_file}: {e}")
                    total_failed += 1
                    continue

                # Evaluate
                try:
                    evaluation = evaluate_document(
                        extracted_data, ground_truth_data, doc_type
                    )

                    # Add OCR metrics if OCR text and ground truth OCR text are available
                    ocr_metrics = {}
                    ocr_text = result_data.get("ocr_text", "")
                    gt_ocr_text = ground_truth_data.get("ocr_text", "")

                    if ocr_text and gt_ocr_text:
                        try:
                            cer_score = cer(gt_ocr_text, ocr_text)
                            wer_score = wer(gt_ocr_text, ocr_text)
                            ocr_metrics = {
                                "cer": cer_score,
                                "wer": wer_score,
                            }
                        except Exception as e:
                            print(f"[WARNING] Failed to compute OCR metrics: {e}")

                    evaluation["metadata"] = {
                        "doc_type": doc_type,
                        "lang": lang,
                        "quality": result_data.get("quality", "unknown"),
                        "file_type": result_data.get("file_type", "unknown"),
                        "source_file": result_data.get("source_file", ""),
                    }

                    if ocr_metrics:
                        evaluation["ocr"] = ocr_metrics

                    # Save evaluation
                    eval_file = eval_lang_dir / f"{base_name}_evaluation.json"
                    eval_file.write_text(
                        json.dumps(evaluation, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )

                    eval_count = total_evaluated - total_failed
                    print(
                        f"[{eval_count}/{total_evaluated}] Evaluated {result_file.name}"
                    )
                except Exception as e:
                    print(f"[ERROR] Failed to evaluate {result_file.name}: {e}")
                    total_failed += 1

    print()
    print("=" * 70)
    print("Evaluation complete!")
    print(f"Total documents evaluated: {total_evaluated - total_failed}")
    print(f"Failed: {total_failed}")
    print("=" * 70)


if __name__ == "__main__":
    main()
