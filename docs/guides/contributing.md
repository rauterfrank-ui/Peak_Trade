# Contributing to Peak Trade

Thank you for your interest in contributing to Peak Trade! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [CI/CD Pipeline](#cicd-pipeline)

## Code of Conduct

- Be respectful and constructive
- Focus on the code, not the person
- Help others learn and improve
- Follow project conventions and standards

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/Peak_Trade.git
cd Peak_Trade
```

### 2. Set Up Development Environment

**macOS (Recommended):**
```bash
bash scripts/setup_macos.sh
source venv/bin/activate
```

**Linux/Other:**
```bash
python3.11 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
```

### 3. Verify Setup

```bash
make validate-env
make test-fast
```

## Development Workflow

### 1. Create a Branch

```bash
# Create a feature branch from main
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements
- `chore/` - Maintenance tasks

### 2. Make Changes

```bash
# Make your changes
# Edit files...

# Check code quality frequently
make lint          # Check linting
make lint-fix      # Auto-fix issues
make typecheck     # Check types
make test          # Run tests
```

### 3. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message (see guidelines below)
git commit -m "feat: Add new risk model implementation"

# Pre-commit hooks will run automatically
```

### 4. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Fill out the PR template completely
```

## Code Quality Standards

### Python Style Guide

We use **Ruff** for linting and formatting:

```bash
# Check code style
make lint

# Auto-fix issues
make lint-fix
```

**Key Style Rules:**
- Line length: 100 characters
- Use type hints where possible
- Follow PEP 8 naming conventions
- Write docstrings for public APIs
- Keep functions focused and small

**Example:**

```python
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Calculate annualized Sharpe ratio.

    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Trading periods per year

    Returns:
        Annualized Sharpe ratio
    """
    excess_returns = returns - risk_free_rate / periods_per_year
    return (
        excess_returns.mean() / excess_returns.std() * (periods_per_year ** 0.5)
    )
```

### Type Checking

We use **MyPy** for static type checking:

```bash
make typecheck
```

**Type Hints Guidelines:**
- Add type hints to all function signatures
- Use `Optional[T]` for nullable values
- Use `Union[T1, T2]` for multiple types
- Import types from `typing` module

### Security Scanning

We scan for security vulnerabilities:

```bash
make security
```

This runs:
- **Bandit** - Python security linter
- **Safety** - Dependency vulnerability checker
- **pip-audit** - PyPI package auditor

## Testing Guidelines

### Writing Tests

**Test Structure:**
```python
# tests/test_feature.py
import pytest
from src.module import YourClass


class TestYourClass:
    """Test YourClass functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.instance = YourClass()

    def test_basic_functionality(self):
        """Test basic feature works correctly."""
        result = self.instance.method()
        assert result == expected_value

    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            self.instance.method(invalid_input)
```

**Test Categories (use markers):**

```python
@pytest.mark.slow
def test_expensive_operation():
    """Mark slow tests."""
    pass

@pytest.mark.integration
def test_system_integration():
    """Mark integration tests."""
    pass
```

### Running Tests

```bash
# Run all tests
make test

# Run fast tests only
make test-fast

# Run with coverage
make coverage

# Run specific test file
pytest tests/test_specific.py -v

# Run specific test
pytest tests/test_specific.py::TestClass::test_method -v
```

### Coverage Requirements

- Aim for **>80% code coverage** for new code
- Test both success and error paths
- Include edge cases and boundary conditions
- Write integration tests for critical paths

## Commit Message Guidelines

We follow **Conventional Commits** format:

```
<type>(<scope>): <short summary>

<detailed description>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements
- `ci:` - CI/CD changes

**Examples:**

```bash
# Feature
git commit -m "feat(risk): Add Kelly criterion position sizing"

# Bug fix
git commit -m "fix(backtest): Correct fee calculation in shadow execution"

# Documentation
git commit -m "docs: Update strategy development guide"

# Breaking change
git commit -m "feat(api)!: Change portfolio API signature

BREAKING CHANGE: Portfolio.add_position() now requires position_size parameter"
```

## Pull Request Process

### 1. Before Creating PR

**Run full quality checks:**
```bash
make ci-local
```

This simulates the CI pipeline locally and ensures:
- ✅ All tests pass
- ✅ Code is properly linted
- ✅ Type checking passes
- ✅ Security scans pass
- ✅ Coverage meets threshold

### 2. Create Pull Request

1. Go to GitHub and create a PR from your branch
2. Fill out the PR template completely:
   - **Description**: What and why
   - **Type of Change**: Select appropriate checkboxes
   - **Testing**: Describe test coverage
   - **Checklist**: Complete all items
   - **Screenshots**: If UI changes

### 3. PR Review Process

**Automated Checks:**
- CI pipeline runs automatically
- All workflows must pass (quality, tests, docs)
- Code coverage is checked
- Security scans must pass

**Human Review:**
- At least one approval required
- Address all review comments
- Update code based on feedback
- Re-request review after changes

### 4. Merging

- PRs are merged via **squash and merge**
- Ensure commit message is clean and follows guidelines
- Delete branch after merge

## CI/CD Pipeline

Our CI/CD pipeline runs automatically on every push and PR.

### Workflows

**1. Quality Checks** (`.github/workflows/quality.yml`)
- Linting with Ruff
- Type checking with MyPy
- Security scanning (Bandit, Safety, pip-audit)
- Tests with coverage (Python 3.10, 3.11, 3.12)

**2. Main CI** (`.github/workflows/ci.yml`)
- Core tests on multiple Python versions
- Platform tests (Linux, macOS)
- Strategy smoke tests
- RL v0.1 contract validation

**3. Documentation** (`.github/workflows/docs.yml`)
- Build and validate documentation
- Check for broken links
- Generate API docs

**4. Dependency Updates** (`.github/workflows/dependency-update.yml`)
- Weekly automated dependency checks
- Security vulnerability scanning
- Update reports as artifacts

### Local CI Simulation

Run the same checks locally before pushing:

```bash
make ci-local
```

This ensures your code will pass CI before creating a PR.

## Feature Flags

We use feature flags for gradual rollouts and safe deployments.

**Usage:**

```python
from src.core.feature_flags import FeatureFlags

# Simple flag check
if FeatureFlags.is_enabled("new_risk_model"):
    use_new_risk_calculation()

# User-based rollout
if FeatureFlags.is_enabled_for_user("ai_signals", user_id):
    show_ai_signals()
```

**Configuration** in `config.toml`:

```toml
[feature_flags]
enable_experimental_strategies = false
enable_ai_risk_advisor = true

[feature_flags.rollout]
new_portfolio_optimizer = 0.1  # 10% rollout
```

See `docs/guides/feature-flags.md` for detailed guide.

## Getting Help

- **Documentation:** Browse `docs/` directory
- **Issues:** Search existing GitHub issues
- **Discussions:** Ask questions in GitHub Discussions
- **Code Examples:** Check `scripts/demo_*.py` files

## Development Tips

### IDE Setup

**VS Code Extensions:**
- Ruff (charliermarsh.ruff)
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)

**PyCharm:**
- Enable Ruff plugin
- Configure Python interpreter to use venv
- Enable type checking

### Useful Commands

```bash
# Quick quality check
make lint typecheck

# Run specific test pattern
pytest -k "test_strategy" -v

# Debug test
pytest tests/test_file.py::test_name --pdb

# Update dependencies
pip list --outdated

# Clean build artifacts
make clean
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:
- Ruff linting and formatting
- MyPy type checking
- Bandit security checks
- File formatting checks

**Skip hooks** (use sparingly):
```bash
git commit --no-verify
```

**Update hooks:**
```bash
pre-commit autoupdate
```

## Code Review Guidelines

When reviewing PRs:

### What to Look For

**Code Quality:**
- Clear and readable code
- Appropriate abstractions
- Proper error handling
- Good test coverage

**Security:**
- No hardcoded secrets
- Input validation
- Proper authorization checks

**Performance:**
- No obvious performance issues
- Efficient algorithms
- Appropriate data structures

**Documentation:**
- Clear docstrings
- Updated README/docs if needed
- Inline comments for complex logic

### Review Etiquette

- Be constructive and specific
- Praise good code
- Ask questions rather than make demands
- Suggest alternatives with reasoning
- Approve when ready, don't nitpick

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag
4. GitHub Actions builds and publishes
5. Update documentation

## Additional Resources

- **Architecture:** `docs/architecture/`
- **Strategy Development:** `docs/STRATEGY_DEV_GUIDE.md`
- **Feature Flags:** `docs/guides/feature-flags.md`
- **CI/CD Architecture:** `docs/architecture/ci-cd.md`
- **macOS Setup:** `docs/guides/macos-setup.md`

---

**Questions?** Open an issue or discussion on GitHub.

**Last Updated:** December 2024
