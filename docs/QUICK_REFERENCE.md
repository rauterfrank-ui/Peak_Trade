# Peak_Trade Quick Reference Card

> **Purpose:** Fast lookup for common commands, patterns, and workflows
>
> **Print this out and keep it handy!**

---

## Essential Commands

### Setup & Health
```bash
# Initial setup
python scripts/dev_workflow.py setup

# Quick health check
python scripts/dev_workflow.py health

# Activate environment
source .venv/bin/activate
```

### Testing
```bash
# All tests
python scripts/dev_workflow.py test

# Specific module
python scripts/dev_workflow.py test --module performance

# With coverage
python scripts/dev_workflow.py test --coverage

# Quick test
pytest tests/test_basics.py -q
```

### Code Quality
```bash
# Run linters
python scripts/dev_workflow.py lint

# Format code
black src/ tests/

# Check types
mypy src/
```

### Research & Trading
```bash
# Run backtest
python scripts/run_backtest.py --strategy ma_crossover

# Portfolio research
python scripts/research_cli.py portfolio --config config/config.toml

# Live ops health
python scripts/live_ops.py health --config config/config.toml
```

---

## Key File Locations

### Source Code
- `src/core/` - Core utilities (config, risk, performance)
- `src/strategies/` - Trading strategies
- `src/backtest/` - Backtest engine
- `src/live/` - Live trading components
- `src/data/` - Data loading and caching

### Configuration
- `config.toml` - Main configuration
- `config/portfolio_recipes.toml` - Portfolio presets
- `pyproject.toml` - Project dependencies

### Documentation
- `README.md` - Main landing page
- `docs/KNOWLEDGE_BASE_INDEX.md` - Documentation hub
- `docs/GETTING_STARTED.md` - First hour guide
- `docs/ai/AI_WORKFLOW_GUIDE.md` - AI usage patterns

---

## Common Workflows

### Add New Strategy
```bash
# 1. Generate scaffold
python scripts/dev_workflow.py create-strategy "My Strategy"

# 2. Edit files
# - src/strategies/my_strategy.py
# - tests/strategies/test_my_strategy.py

# 3. Test
python scripts/dev_workflow.py test --module strategies/test_my_strategy

# 4. Run backtest
python scripts/run_backtest.py --strategy my_strategy
```

### Debug Test Failure
```bash
# 1. Run specific test with verbose
pytest tests/test_module.py::TestClass::test_method -vv

# 2. Add debug output
# In code: import logging; logging.basicConfig(level=logging.DEBUG)

# 3. Use debugger
pytest tests/test_module.py --pdb

# 4. Check performance
python scripts/dev_workflow.py perf-check
```

### Performance Profiling
```python
from src.core.performance import performance_monitor

# Time an operation
with performance_monitor.measure("my_operation"):
    # Your code here
    pass

# Get metrics
performance_monitor.print_summary()
```

---

## Git Shortcuts

### Branch Operations
```bash
# Create feature branch
git checkout -b feature/my-feature

# Update from main
git pull origin main

# Push changes
git push origin feature/my-feature
```

### Commit Messages
```
feat(scope): add new feature
fix(scope): fix bug
docs(scope): update documentation
test(scope): add tests
refactor(scope): refactor code
perf(scope): improve performance
```

---

## Import Patterns

### Common Imports
```python
# Configuration
from src.core import PeakConfig, load_peak_config

# Performance monitoring
from src.core.performance import performance_monitor, performance_timer

# Error handling
from src.core.errors import PeakTradeError, ConfigError

# Resilience
from src.core.resilience import circuit_breaker, retry_with_backoff

# Strategy base
from src.strategies.base import BaseStrategy, Signal
```

---

## Testing Patterns

### Basic Test Structure
```python
import pytest
from src.module import MyClass

class TestMyClass:
    def test_init(self):
        obj = MyClass()
        assert obj is not None
    
    def test_method(self):
        obj = MyClass()
        result = obj.method()
        assert result == expected
```

### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

---

## Performance Tips

### Quick Wins
- Use `@performance_timer` decorator on slow functions
- Cache frequently accessed data with `@lru_cache`
- Use vectorized operations (numpy/pandas) instead of loops
- Profile before optimizing: `python -m cProfile script.py`

### Monitoring
```python
from src.core.performance import performance_monitor

# During development
@performance_timer("my_function")
def my_function():
    pass

# In production
with performance_monitor.measure("operation"):
    # Critical path
    pass
```

---

## Safety Checklist

### Before Committing
- [ ] All tests pass
- [ ] Linters pass
- [ ] Documentation updated
- [ ] No TODO/FIXME in committed code
- [ ] No secrets or credentials
- [ ] No live trading activated

### Code Review
- [ ] Follows Peak_Trade patterns
- [ ] Has comprehensive tests
- [ ] Documented with examples
- [ ] No performance regressions
- [ ] Backward compatible

---

## Help & Resources

### Quick Help
```bash
# Script help
python scripts/dev_workflow.py --help

# Test help
pytest --help

# Git help
git <command> --help
```

### Documentation
- Main: [README.md](../README.md)
- Knowledge Base: [KNOWLEDGE_BASE_INDEX.md](KNOWLEDGE_BASE_INDEX.md)
- Workflows: [DEVELOPER_WORKFLOW_GUIDE.md](DEVELOPER_WORKFLOW_GUIDE.md)
- AI Guide: [ai/AI_WORKFLOW_GUIDE.md](ai/AI_WORKFLOW_GUIDE.md)

### Getting Stuck?
1. Check [Knowledge Base Index](KNOWLEDGE_BASE_INDEX.md)
2. Run `python scripts/dev_workflow.py health`
3. Search codebase for similar patterns
4. Review test files for examples
5. Check AI workflow guide for prompt templates

---

## Keyboard Shortcuts (VS Code)

- `Cmd/Ctrl + Shift + T` - Run tests
- `Cmd/Ctrl + Shift + B` - Run linters
- `Cmd/Ctrl + P` - Quick file open
- `Cmd/Ctrl + Shift + F` - Search in files
- `F5` - Start debugging
- `Shift + F5` - Stop debugging

---

## Emergency Procedures

### Tests Broken
```bash
# 1. Check what changed
git status
git diff

# 2. Run specific failing test
pytest tests/test_module.py::test_name -vv

# 3. Reset if needed
git checkout -- <file>

# 4. Verify fix
python scripts/dev_workflow.py test
```

### Performance Degraded
```bash
# 1. Run performance check
python scripts/dev_workflow.py perf-check

# 2. Profile the operation
python -m cProfile -o profile.stats script.py

# 3. Analyze
python -m pstats profile.stats

# 4. Optimize and re-check
```

### Environment Broken
```bash
# 1. Clean environment
rm -rf .venv
rm -rf .pytest_cache
rm -rf src/*.egg-info

# 2. Rebuild
python scripts/dev_workflow.py setup

# 3. Verify
python scripts/dev_workflow.py health
```

---

**Print Date:** 2025-12-19 | **Version:** 1.0

**Navigation:** [📚 Knowledge Base](KNOWLEDGE_BASE_INDEX.md) | [🏠 README](../README.md)
