# Architecture: Unified Document Extraction Framework

## Structure

Unified, configuration-driven architecture supporting multiple document types:

### `core/` - Generic Framework
- **`ocr.py`** - OCR extraction
- **`extractor.py`** - LLM-based structured extraction with schema transformation
- **`visualizer.py`** - PDF annotation with OCR boxes and legend

### Unified Modules
- **`unified_extractor.py`** - Single extraction function for all document types
- **`unified_visualizer.py`** - Single visualization function for all document types
- **`document_config/config.py`** - Centralized configuration (models, prompts, legends, redaction)

### Document-Specific Models
- **`deliverynote/models.py`** - `DeliveryNoteReport`, `ProductoLinea`
- **`bank/models.py`** - `BankStatement`, `BankLine`
- **`payroll/models.py`** - `PayrollReport`, `Devengo`, `Deduccion`

## Usage

```python
from document_llm_extractor.core.ocr import extract_ocr
from document_llm_extractor.unified_extractor import extract_document
from document_llm_extractor.unified_visualizer import annotate_document_pdf

ocr_result = extract_ocr("document.pdf")
report = extract_document("deliverynote", ocr_result["text"])
annotate_document_pdf("deliverynote", "input.pdf", report, ocr_result["ocr_items"], "output.pdf")
```

## Adding a New Document Type

1. Create `invoice/models.py` with Pydantic models
2. Register in `document_config/config.py`:
   ```python
   DOCUMENT_CONFIGS["invoice"] = DocumentConfig(
       model_class=InvoiceReport,
       system_prompt="Extract invoice information...",
       user_prompt_template="Extract from: {text}",
       make_legend_lines=lambda r: [f"Invoice: {r.invoice_number}"],
   )
   ```
3. Use: `extract_document("invoice", ocr_text)`

## Extraction Flow

1. **OCR** (`core/ocr.py`) - Extracts text and bounding boxes
2. **Configuration** (`document_config/config.py`) - Retrieves document-specific config (model, prompts, text limit, legend, redaction)
3. **Unified Extraction** (`unified_extractor.py`) - Applies text limits, calls core extractor
4. **Core LLM Extraction** (`core/extractor.py`) - Converts Pydantic schema, transforms for OpenAI strict mode, calls LLM, validates, retries up to 3 times

## Document Type Definitions

### Delivery Note
- **Models**: `DeliveryNoteReport` (metadata, supplier, products, financial), `ProductoLinea`
- **Config**: Spanish extraction prompts, no text limit

### Bank Statements
- **Models**: `BankStatement` (account, period, transactions, balances), `BankLine`
- **Config**: Spanish prompts, 40k char limit, transaction format (negative=expense, positive=income)

### Payroll
- **Models**: `PayrollReport` (identifiers, earnings, deductions, totals), `Devengo`, `Deduccion`
- **Config**: Spanish prompts, 40k char limit, custom redaction

## Data Flow

```
PDF → OCR → text + ocr_items → unified_extractor → Pydantic model → unified_visualizer → Annotated PDF
```
