# Development Tooling

This document describes the development tools used in Peak Trade.

## Package Manager: uv

We use [uv](https://docs.astral.sh/uv/) as our Python package manager. It's fast, reliable, and handles virtual environments automatically.

After syncing dependencies, activate the virtual environment and run tools directly.

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

# Activate the virtual environment (macOS/Linux)
source .venv/bin/activate

# Add a new dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Run tests
python3 -m pytest tests/

# Run a script
python3 scripts/my_script.py
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
ruff check src tests scripts

# Check with auto-fix
ruff check src tests scripts --fix

# Format code
ruff format src tests scripts

# Check formatting without changing files
ruff format --check src tests scripts
```

## Pre-commit Hooks

We use [pre-commit](https://pre-commit.com/) to run checks before each commit.

### Setup

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run a specific hook
pre-commit run ruff --all-files
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

# 3. Activate virtual environment
source .venv/bin/activate

# 3. Set up pre-commit hooks
pre-commit install

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
pre-commit run --all-files -v
```

### Ruff finds many errors in existing code

The conservative gate ignores most legacy issues. If you see errors, they're likely new issues that should be fixed.
