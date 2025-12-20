# Developer Onboarding Guide

## Quick Start (1 hour setup)

### 1. Clone Repository

```bash
git clone https://github.com/rauterfrank-ui/Peak_Trade.git
cd Peak_Trade
```

### 2. Automated Setup

Run the interactive onboarding script:

```bash
python scripts/onboard.py
```

This will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Set up pre-commit hooks
- ✅ Configure IDE (VSCode/PyCharm)
- ✅ Run verification tests

### 3. Manual Verification

```bash
# Activate environment
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Run tests
pytest tests/

# Check code quality
python scripts/code_review.py
```

## Development Workflow

### Daily Commands

```bash
# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_workflows.py

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Lint code
ruff check .

# Format code
ruff format .

# Type check
mypy src/

# Security scan
bandit -r src/ -ll

# Full quality check
python scripts/code_review.py
```

### Pre-commit Hooks

Hooks run automatically on `git commit`:

```bash
# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

### Creating a Strategy

```bash
# Use the strategy development script
python scripts/research_cli.py create-strategy "My Strategy"

# Or manually create in src/strategies/
```

### Feature Flags

Enable experimental features in `config/feature_flags.json`:

```json
{
  "enable_experimental_strategies": {
    "enabled": true
  }
}
```

In code:

```python
from src.core.feature_flags import feature_flags, FeatureFlag

if feature_flags.is_enabled(FeatureFlag.ENABLE_EXPERIMENTAL_STRATEGIES):
    use_experimental_strategy()
```

## IDE Setup

### VSCode

Install recommended extensions:
- Python
- Ruff
- MyPy
- Jupyter (optional)

Settings are configured by `onboard.py` in `.vscode/settings.json`.

### PyCharm

1. Open project
2. Configure Python interpreter: `venv/bin/python`
3. Enable Ruff: Settings → Tools → Ruff
4. Enable MyPy: Settings → Tools → External Tools → MyPy

## Troubleshooting

### Apple Silicon (M2/M3)

If NumPy fails to install:

```bash
brew install openblas
pip install numpy --no-binary :all:
```

### Pre-commit Fails

Update dependencies:

```bash
pre-commit clean
pre-commit install
pre-commit run --all-files
```

### Tests Fail

Check environment:

```bash
# Verify Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt

# Run basic smoke test
pytest tests/test_basics.py -v
```

## Getting Help

- **Documentation**: [https://rauterfrank-ui.github.io/Peak_Trade](https://rauterfrank-ui.github.io/Peak_Trade)
- **Issues**: [GitHub Issues](https://github.com/rauterfrank-ui/Peak_Trade/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rauterfrank-ui/Peak_Trade/discussions)

## Next Steps

1. Read [Architecture Overview](../architecture/overview.md)
2. Try [Quick Start Tutorial](quickstart.md)
3. Explore [Strategy Development Guide](../guides/strategy-development.md)
4. Review [API Reference](../api/core.md)

## Contributing

See [Contributing Guide](../development/contributing.md) for:
- Code style guidelines
- Pull request process
- Testing requirements
- Documentation standards
