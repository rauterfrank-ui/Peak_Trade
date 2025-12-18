# Development Tooling

This document describes the development tools used in Peak Trade.

## Package Manager: uv

We use [uv](https://docs.astral.sh/uv/) as our Python package manager. It's fast, reliable, and handles virtual environments automatically.

### Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

### Common Commands

```bash
# Install all dependencies (creates .venv automatically)
uv sync

# Install with dev dependencies
uv sync --dev

# Add a new dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Run a command in the virtual environment
uv run <command>

# Run tests
uv run pytest tests/

# Run a script
uv run python scripts/my_script.py
```

## Linting: ruff

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting. It's extremely fast and replaces multiple tools (flake8, isort, black).

### Configuration

Ruff is configured in `pyproject.toml`. We use a **conservative gate** to avoid churn in legacy code:

- **Selected rules**: `E` (pycodestyle errors), `F` (pyflakes)
- **Ignored rules**:
  - `E402`: module level import not at top of file
  - `E501`: line too long (handled by formatter)
  - `F401`: imported but unused (many `__init__.py` re-exports)
  - `F841`: local variable assigned but never used

### Manual Commands

```bash
# Check for lint errors
uv run ruff check src tests scripts

# Check with auto-fix
uv run ruff check src tests scripts --fix

# Format code
uv run ruff format src tests scripts

# Check formatting without changing files
uv run ruff format --check src tests scripts
```

## Pre-commit Hooks

We use [pre-commit](https://pre-commit.com/) to run checks before each commit.

### Setup

```bash
# Install pre-commit hooks (one-time setup)
uv run pre-commit install

# Run all hooks manually
uv run pre-commit run --all-files

# Run a specific hook
uv run pre-commit run ruff --all-files
```

### Configured Hooks

1. **ruff** - Linter with auto-fix
2. **ruff-format** - Code formatter
3. **trailing-whitespace** - Remove trailing whitespace
4. **end-of-file-fixer** - Ensure files end with newline
5. **check-yaml** - Validate YAML syntax
6. **check-added-large-files** - Prevent large files (>500KB)
7. **check-merge-conflict** - Detect merge conflict markers

## CI Workflow

The lint workflow (`.github/workflows/lint.yml`) runs on:
- Push to `main`
- Pull requests to `main`

It only triggers when Python files in `src/`, `tests/`, or `scripts/` change (path-filtered).

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd peak_trade

# 2. Install dependencies
uv sync --dev

# 3. Set up pre-commit hooks
uv run pre-commit install

# 4. You're ready! Pre-commit will run automatically on git commit
```

## Troubleshooting

### "command not found: uv"

Add uv to your PATH:
```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
```

### Pre-commit hooks fail

Run hooks manually to see details:
```bash
uv run pre-commit run --all-files -v
```

### Ruff finds many errors in existing code

The conservative gate ignores most legacy issues. If you see errors, they're likely new issues that should be fixed.
