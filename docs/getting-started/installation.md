# Installation

## Prerequisites

- Python 3.9 or higher
- pip or uv package manager
- Virtual environment (recommended)

## Quick Installation

### Using pip

```bash
# Clone the repository
git clone https://github.com/rauterfrank-ui/Peak_Trade.git
cd Peak_Trade

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov ruff mypy bandit
```

### Using Automated Setup

Run the interactive onboarding script:

```bash
python scripts/onboard.py
```

This will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Set up pre-commit hooks
- ✅ Configure IDE settings
- ✅ Run verification tests

## Apple Silicon (M2/M3)

Peak Trade is optimized for Apple Silicon. If you encounter NumPy installation issues:

```bash
brew install openblas
pip install numpy --no-binary :all:
```

## Verify Installation

```bash
# Run basic tests
pytest tests/test_basics.py

# Check configuration
python -c "import src; print('✅ Peak Trade installed successfully')"
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Configuration](configuration.md)
- [Development Setup](../development/contributing.md)
