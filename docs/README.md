# Documentation

This directory contains development and project documentation.

## Available Documentation

- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - Complete guide for developers
  - Development environment setup
  - Running tests
  - Pre-commit hooks
  - Development tools (Ruff, MyPy, Pytest, UV)
  - Code quality guidelines
  - CI/CD information

- **[STATISTICS_GRAPHS.md](./STATISTICS_GRAPHS.md)** - Statistics and visualization guide
  - Explanation of all generated graphs
  - Understanding extraction metrics
  - Tips for analyzing results
  - How to interpret each visualization

## Quick Links

### For New Contributors

1. Read [DEVELOPMENT.md](./DEVELOPMENT.md) for setup instructions
2. Install dependencies: `uv sync`
3. Install pre-commit hooks: `uv run pre-commit install`
4. Run tests: `uv run pytest`

### Common Tasks

- **Run tests:** `uv run pytest`
- **Run linters:** `uv run ruff check src tests tools && uv run mypy src/`
- **Format code:** `uv run ruff format src tests tools`
- **Check formatting:** `uv run ruff format --check src tests tools`
- **Run pre-commit hooks:** `uv run pre-commit run --all-files`

## Project Structure

```
albaran_docling/
├── docs/              # Documentation (this directory)
├── src/               # Source code
├── tests/             # Test suite
├── tools/             # Utility scripts
├── .github/           # GitHub Actions workflows
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── pyproject.toml     # Project configuration
├── ruff.toml          # Ruff linter configuration
├── mypy.ini           # MyPy type checker configuration
└── pytest.ini         # Pytest configuration
```
