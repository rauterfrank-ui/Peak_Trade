# Contributing to Peak Trade

Thank you for your interest in contributing to Peak Trade!

## Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Peak_Trade.git
   cd Peak_Trade
   ```
3. **Set up development environment**:
   ```bash
   python scripts/onboard.py
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-new-feature
```

Branch naming conventions:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring

### 2. Make Changes

Follow the code style guidelines below.

### 3. Run Quality Checks

```bash
# Format code
ruff format .

# Run all checks
python scripts/code_review.py

# Or use Makefile
make check
```

### 4. Add Tests

All new features must include tests:

```python
# tests/test_my_feature.py
def test_my_new_feature():
    """Test description."""
    # Arrange
    input_data = create_test_data()

    # Act
    result = my_new_feature(input_data)

    # Assert
    assert result.is_valid
    assert result.value > 0
```

### 5. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_my_feature.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### 6. Commit Changes

Use conventional commit messages:

```bash
git commit -m "feat: add new strategy for momentum trading"
git commit -m "fix: correct position sizing calculation"
git commit -m "docs: update installation guide"
```

Commit types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### 7. Push and Create PR

```bash
git push origin feature/my-new-feature
```

Then create a Pull Request on GitHub.

## Code Style

### Python Style

- **Line length**: 100 characters
- **Imports**: Sorted with isort (via Ruff)
- **Formatting**: Ruff format
- **Type hints**: Use where possible
- **Docstrings**: Google style

Example:

```python
from typing import Optional
import pandas as pd
from src.strategies.base import BaseStrategy


class MyStrategy(BaseStrategy):
    """
    Brief description of strategy.

    Longer description with more details about
    the strategy logic and usage.

    Args:
        period: Lookback period for calculations
        threshold: Signal threshold value

    Example:
        ```python
        strategy = MyStrategy(period=20, threshold=0.05)
        signals = strategy.generate_signals(data)
        ```
    """

    def __init__(self, period: int = 20, threshold: float = 0.05):
        super().__init__()
        self.period = period
        self.threshold = threshold

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.

        Args:
            data: OHLCV market data

        Returns:
            Series of signals: 1 (buy), -1 (sell), 0 (hold)

        Raises:
            ValueError: If data is invalid
        """
        if data.empty:
            raise ValueError("Data cannot be empty")

        # Implementation
        signals = pd.Series(0, index=data.index)
        return signals
```

### Documentation Style

- **Clear and concise**: Get to the point quickly
- **Code examples**: Include working examples
- **Parameters**: Document all parameters
- **Return values**: Document return types
- **Exceptions**: Document exceptions raised

## Testing Guidelines

### Test Structure

```python
def test_feature_name():
    """Test description following Arrange-Act-Assert pattern."""
    # Arrange: Set up test data
    data = create_test_data()
    strategy = MyStrategy(period=20)

    # Act: Execute the code under test
    result = strategy.generate_signals(data)

    # Assert: Verify expected behavior
    assert len(result) == len(data)
    assert result.isin([-1, 0, 1]).all()
```

### Test Coverage

- Aim for **>80% coverage** for new code
- Test happy paths and edge cases
- Test error conditions
- Use fixtures for common test data

### Test Organization

```
tests/
├── test_basics.py           # Basic smoke tests
├── test_workflows.py        # Workflow automation tests
├── strategies/
│   ├── test_ma_crossover.py
│   └── test_rsi_strategy.py
├── backtest/
│   ├── test_engine.py
│   └── test_stats.py
└── conftest.py             # Shared fixtures
```

## Pull Request Process

### PR Checklist

Before submitting:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] PR description is clear

### PR Description

Use this template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
How have you tested these changes?

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code follows style guide
```

### Review Process

1. **Automated checks** run on PR
2. **Code review** by maintainers
3. **Address feedback** if needed
4. **Merge** when approved

## Feature Flags

New experimental features should use feature flags:

```python
from src.core.feature_flags import requires_feature, FeatureFlag

@requires_feature(FeatureFlag.ENABLE_EXPERIMENTAL_STRATEGIES)
def experimental_feature():
    """This feature is gated behind a flag."""
    pass
```

Add new flags to `config/feature_flags.json` and `src/core/feature_flags.py`.

## Documentation

### Building Docs

```bash
# Generate API docs
python scripts/generate_docs.py

# Build documentation
mkdocs build

# Serve locally
mkdocs serve
```

### Adding Documentation

- User guides: `docs/guides/`
- Architecture: `docs/architecture/`
- API reference: Auto-generated from docstrings

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email security concerns privately

## Code of Conduct

Be respectful and constructive in all interactions.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (Proprietary).
