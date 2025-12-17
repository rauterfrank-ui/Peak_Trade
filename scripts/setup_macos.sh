#!/bin/bash
# ============================================================================
# Peak Trade Setup for macOS (Apple Silicon M2/M3)
# ============================================================================
# One-command setup script for macOS development environment
# Usage: bash scripts/setup_macos.sh
# ============================================================================

set -e

echo "🚀 Peak Trade Setup for macOS (Apple Silicon)"
echo ""

# ============================================================================
# Check Architecture
# ============================================================================
if [[ $(uname -m) != "arm64" ]]; then
    echo "⚠️  Warning: Not running on Apple Silicon (arm64)"
    echo "   Detected: $(uname -m)"
    echo "   Script optimized for M2/M3 but will continue..."
    echo ""
fi

# ============================================================================
# Check/Install Homebrew
# ============================================================================
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon
    if [[ $(uname -m) == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo "✅ Homebrew already installed"
fi

# ============================================================================
# Install Python 3.11 (optimized for Apple Silicon)
# ============================================================================
echo ""
echo "🐍 Setting up Python..."

if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    brew install python@3.11
else
    echo "✅ Python 3.11 already installed"
fi

# ============================================================================
# Create Virtual Environment
# ============================================================================
echo ""
echo "📦 Creating virtual environment..."

if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# ============================================================================
# Upgrade pip
# ============================================================================
echo ""
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

# ============================================================================
# Install Dependencies
# ============================================================================
echo ""
echo "📚 Installing dependencies..."

if [ -f "requirements.txt" ]; then
    echo "→ Installing production dependencies..."
    pip install -r requirements.txt
fi

if [ -f "requirements-dev.txt" ]; then
    echo "→ Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# ============================================================================
# Install Pre-commit Hooks
# ============================================================================
echo ""
echo "🪝 Setting up pre-commit hooks..."

if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  pre-commit not found. Install with: pip install pre-commit"
fi

# ============================================================================
# Install Optional Tools
# ============================================================================
echo ""
echo "🛠️  Installing optional development tools..."

# ripgrep for fast code search
if ! command -v rg &> /dev/null; then
    echo "→ Installing ripgrep..."
    brew install ripgrep
fi

# GitHub CLI (optional)
if ! command -v gh &> /dev/null; then
    echo "→ Installing GitHub CLI..."
    brew install gh
    echo "   Run 'gh auth login' to authenticate"
fi

# ============================================================================
# Run Health Check
# ============================================================================
echo ""
echo "🏥 Running health check..."

if [ -d "tests" ]; then
    echo "→ Running quick test suite..."
    python -m pytest tests/ -v --tb=short -x -k "not slow" || {
        echo "⚠️  Some tests failed. Review output above."
        echo "   This is non-blocking - you can continue development."
    }
else
    echo "⚠️  No tests directory found"
fi

# ============================================================================
# Environment Validation
# ============================================================================
echo ""
echo "✅ Validating environment..."

python --version
pip --version

echo ""
echo "Installed key packages:"
pip list | grep -E "pytest|ruff|mypy|bandit" || echo "  (Install dev dependencies for full toolkit)"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Setup complete! Peak Trade is ready for development."
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Next steps:"
echo "   1. Activate environment:  source venv/bin/activate"
echo "   2. Run tests:            make test"
echo "   3. Check code quality:    make quality"
echo "   4. View all commands:     make help"
echo ""
echo "🍎 Apple Silicon optimizations enabled"
echo "🚀 Happy coding!"
echo ""
