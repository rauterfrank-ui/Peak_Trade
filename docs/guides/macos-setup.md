# macOS Setup Guide for Peak Trade

Complete setup guide for developing Peak Trade on macOS with Apple Silicon (M2/M3).

## Prerequisites

- macOS 12.0 or later
- Apple Silicon (M2/M3) recommended (Intel also supported)
- Command Line Tools or Xcode
- ~2GB free disk space

## Quick Start (Recommended)

The fastest way to set up Peak Trade on macOS:

```bash
# Clone the repository
git clone https://github.com/rauterfrank-ui/Peak_Trade.git
cd Peak_Trade

# Run automated setup script
bash scripts/setup_macos.sh

# Activate virtual environment
source venv/bin/activate

# Verify installation
make validate-env
```

The setup script will:
- ✅ Install Homebrew (if not present)
- ✅ Install Python 3.11 (optimized for Apple Silicon)
- ✅ Create and configure virtual environment
- ✅ Install all dependencies
- ✅ Set up pre-commit hooks
- ✅ Install development tools (ripgrep, gh)
- ✅ Run health checks

## Manual Setup

If you prefer to set up manually or need more control:

### 1. Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to PATH (Apple Silicon)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 2. Install Python 3.11

```bash
brew install python@3.11
```

Verify installation:
```bash
python3.11 --version  # Should show Python 3.11.x
```

### 3. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 5. Set Up Pre-commit Hooks

```bash
pre-commit install
```

### 6. Verify Installation

```bash
# Run validation script
python scripts/validate_environment.py

# Run quick tests
make test-fast
```

## Apple Silicon Optimizations

Peak Trade is optimized for Apple Silicon (M2/M3):

### Native ARM64 Support
- Python packages compiled for ARM64
- NumPy and Pandas use Apple's Accelerate framework
- Faster execution compared to Rosetta 2

### Memory Efficiency
- Unified memory architecture leveraged
- Efficient data processing with NumPy/Pandas
- Reduced memory overhead

### Performance Tips
1. Always use native ARM64 Python (not x86_64 via Rosetta)
2. Use Metal-accelerated libraries when available
3. Enable parallel processing with pytest-xdist

## Development Workflow

### Daily Development

```bash
# Activate environment
source venv/bin/activate

# Check code quality before committing
make quality

# Run tests
make test

# Run fast tests only
make test-fast

# Check coverage
make coverage
```

### Code Quality Checks

```bash
# Linting
make lint

# Auto-fix linting issues
make lint-fix

# Type checking
make typecheck

# Security scanning
make security
```

### Running CI Locally

Simulate CI pipeline locally before pushing:

```bash
make ci-local
```

This runs all checks that CI will run:
- Linting (ruff)
- Type checking (mypy)
- Security scanning (bandit, safety, pip-audit)
- Tests with coverage
- Documentation validation

## Common Issues & Solutions

### Issue: Command not found after Homebrew install

**Solution:** Add Homebrew to PATH:
```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Issue: Python version mismatch

**Solution:** Ensure you're using Python 3.11:
```bash
python --version  # Should show 3.11.x
which python      # Should point to venv
```

### Issue: Pre-commit hooks failing

**Solution:** Update pre-commit hooks:
```bash
pre-commit autoupdate
pre-commit run --all-files
```

### Issue: Tests failing on import

**Solution:** Ensure virtual environment is activated and dependencies installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Permission denied on scripts

**Solution:** Make scripts executable:
```bash
chmod +x scripts/*.sh scripts/*.py
```

## Performance Benchmarks

Expected setup times on Apple Silicon M2:
- Automated setup: **~3-5 minutes**
- Manual setup: **~5-8 minutes**
- Test suite: **~1-2 minutes**
- Full CI simulation: **~3-5 minutes**

## Additional Tools

### Optional but Recommended

```bash
# GitHub CLI (for GitHub integration)
brew install gh
gh auth login

# ripgrep (fast code search)
brew install ripgrep

# Better terminal
brew install --cask iterm2

# VS Code (if not using another IDE)
brew install --cask visual-studio-code
```

## IDE Setup

### VS Code Settings (Recommended)

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### VS Code Extensions

```bash
code --install-extension charliermarsh.ruff
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
```

## Next Steps

After setup is complete:

1. **Read the Contributing Guide:** `docs/guides/contributing.md`
2. **Explore the Architecture:** `docs/architecture/`
3. **Run example backtests:** `python scripts/demo_backtest_with_risk.py`
4. **Check feature flags:** `docs/guides/feature-flags.md`
5. **Review CI/CD setup:** `docs/architecture/ci-cd.md`

## Getting Help

- 📚 Documentation: `docs/`
- 🐛 Report bugs: GitHub Issues
- 💬 Questions: GitHub Discussions
- 🔧 Run diagnostics: `make validate-env`

## Updates & Maintenance

```bash
# Update dependencies weekly
pip list --outdated

# Update pre-commit hooks
pre-commit autoupdate

# Check for security vulnerabilities
make security
```

---

**Last Updated:** December 2024  
**Tested On:** macOS 14.x (Apple Silicon M2/M3)  
**Python Version:** 3.11+
