# Development Guide

## Setup

**Prerequisites:**
- Python 3.12
- [uv](https://github.com/astral-sh/uv)
- Tesseract OCR, Poppler utilities

**Installation:**
```bash
# System dependencies (Ubuntu/Debian)
sudo apt-get install -y tesseract-ocr tesseract-ocr-spa tesseract-ocr-cat tesseract-ocr-eng poppler-utils

# Python dependencies
uv sync

# Pre-commit hooks
uv run pre-commit install
```

## Running Tests

```bash
uv run pytest              # All tests
uv run pytest -v           # Verbose
uv run pytest tests/test_models.py  # Specific file
uv run pytest -k "test_deliverynote"  # Pattern match
uv run pytest --cov=src    # With coverage
```

## Development Tools

### Ruff
```bash
uv run ruff check src tests tools        # Lint
uv run ruff check --fix src tests tools  # Auto-fix
uv run ruff format src tests tools       # Format
```

### MyPy
```bash
uv run mypy src/
# Or run both linting tools:
uv run ruff check src tests tools && uv run mypy src/
```

### Pre-commit
```bash
uv run pre-commit run --all-files  # Run all hooks
```

**Hooks:** Ruff (linter/formatter), isort (import sorting), end-of-file-fixer, trailing-whitespace

## Code Quality

- **Line length:** 100 characters
- **Formatter:** Ruff
- **Type hints:** Use where appropriate
- **Docstrings:** Google-style

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):
- Runs on push/PR to `main`
- Checks: ruff lint, ruff format, pytest

**Local CI simulation:**
```bash
uv sync
uv run ruff check src tests tools
uv run ruff format --check src tests tools
OPENAI_API_KEY="sk-test-dummy-key" uv run pytest -q
```
