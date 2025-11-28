# OCR Engines

Select OCR engine via `--ocr-engine` flag. Default: RapidOCR.

## Available Engines

1. **RapidOCR** (default) - Fast ONNX-based engine, optimized for Latin scripts. Supports PDF and images.
2. **Tesseract** - Open-source engine with strong language support. Supports PDF and images.

## Installation

**Tesseract:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa tesseract-ocr-cat tesseract-ocr-eng
```

**RapidOCR:** Automatically installed via `rapidocr-onnxruntime` package.

## Usage

### CLI
```bash
# RapidOCR (default)
document-llm-extractor path/to/document.pdf --output-dir outputs

# Tesseract
document-llm-extractor path/to/document.pdf \
  --ocr-engine tesseract \
  --langs "spa,cat,eng" \
  --tesseract-oem 1 \
  --tesseract-psm 6
```

### Batch Inference
```bash
python tools/batch_inference.py --ocr-engine rapidocr
python tools/batch_inference.py --ocr-engine tesseract --langs "spa,eng"
```

**Output structure:** `outputs/{ocr_engine}/inference/{doc_type}/{lang}/`

## Options

- `--ocr-engine` - `rapidocr` (default) or `tesseract`
- `--langs` - Comma-separated language codes (default: `"spa,cat,eng"`)
- `--tesseract-oem` - Engine mode (0-3, default: 1)
- `--tesseract-psm` - Page segmentation (0-13, default: 6)
- `--tesseract-extra` - Additional Tesseract config

## Notes

- Tesseract requires language-specific packages. Missing languages log warnings.
- RapidOCR doesn't use language tags; `--langs` is ignored.
- All engines support multi-page PDFs with per-page timing.
