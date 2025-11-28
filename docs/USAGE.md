# Usage Guide

## Batch Processing Workflow

```bash
# Step 1: Process documents
python tools/batch_inference.py --ocr-engine rapidocr --doc-type deliverynote --limit 3

# Step 2: Evaluate results
python tools/evaluate_results.py --ocr-engine rapidocr

# Step 3: Generate statistics
python tools/generate_statistics.py --ocr-engine rapidocr

# Step 4: Compare models (optional)
python tools/compare_models.py \
  --eval-dir-A outputs/rapidocr/evaluations/deliverynote/es \
  --eval-dir-B outputs/tesseract/evaluations/deliverynote/es \
  --field "numero_deliverynote"
```

**Options:**
- `--doc-type` - Document type: `deliverynote`, `bank`, `payroll` (default: all)
- `--limit` - Max documents to process
- `--ocr-engine` - `rapidocr` (default) or `tesseract`
- `--langs` - OCR languages (default: `"spa,cat,eng"`)

## Output Files

### Single Document (CLI)
```
outputs/{run_id}/
  raw/
    ocr_text.txt, ocr_markdown.md, extracted_fields.json
  llm/
    llm_responses.json
  viz/
    {input_name}_viz.pdf
```

### Batch Processing
```
outputs/{ocr_engine}/
  inference/{doc_type}/{lang}/
    {filename}.json, {filename}_viz.pdf, {filename}_viz.jpg
  evaluations/{doc_type}/{lang}/
    {filename}_evaluation.json
  statistics/
    field_extraction_stats.json
    plots/*.png
```

Annotated PDFs include: original pages, OCR bounding boxes, extracted fields panel, optional redaction.
