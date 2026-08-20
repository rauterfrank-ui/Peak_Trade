# Peak_Trade Developer Workflow Guide

Python floor: `requires-python = ">=3.10"`. Run Peak_Trade Python only via `./scripts/pt` (see `docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md`). PATH `python`/`python3` is not a supported runtime.

> **Purpose:** Streamlined workflows and automation tools for productive development
>
> **Target Audience:** All developers working on Peak_Trade
>
> **Related:** [Dev Setup](DEV_SETUP.md), [CLI Cheatsheet](CLI_CHEATSHEET.md)

---

## Overview

This guide provides efficient workflows and automation tools to maximize developer productivity while maintaining code quality and safety standards.

---

## Quick Start Workflows

### New Developer - First Day Setup

```bash
# 1. Clone and setup
git clone <repo-url>
cd Peak_Trade

# 2. Automated setup
./scripts/pt scripts/dev_workflow.py setup

# 3. Health check
./scripts/pt scripts/dev_workflow.py health

# 4. Run tests to verify setup
./scripts/pt scripts/dev_workflow.py test --module test_basics

# 5. Read essential docs
# - README.md
# - docs/GETTING_STARTED.md
# - docs/ai/PEAK_TRADE_AI_HELPER_GUIDE.md
```

### Daily Development Workflow

```bash
# Morning routine
./scripts/pt scripts/dev_workflow.py health        # Quick system check
git pull origin main                          # Get latest changes

# During development
./scripts/pt scripts/dev_workflow.py test --module <module>  # Test your changes
./scripts/pt scripts/dev_workflow.py lint                    # Check code style

# Before committing
./scripts/pt scripts/dev_workflow.py test                    # Full test suite
./scripts/pt scripts/dev_workflow.py docs-validate           # Check docs
git add .
git commit -m "Your change description"
git push
```

### Feature Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes incrementally
# ... edit files ...
./scripts/pt scripts/dev_workflow.py test --module <module> -v

# 3. Run linters
./scripts/pt scripts/dev_workflow.py lint

# 4. Validate changes
./scripts/pt scripts/dev_workflow.py health
./scripts/pt scripts/dev_workflow.py docs-validate

# 5. Commit and push
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature-name

# 6. Create pull request
# Open PR via GitHub UI
```

---

## Developer Workflow Script

The `scripts/dev_workflow.py` script automates common development tasks.

### Available Commands

#### Setup Environment
```bash
./scripts/pt scripts/dev_workflow.py setup
```
- Creates virtual environment
- Installs dependencies
- Verifies Python version

#### Run Tests
```bash
# All tests
./scripts/pt scripts/dev_workflow.py test

# Specific module
./scripts/pt scripts/dev_workflow.py test --module performance

# With coverage
./scripts/pt scripts/dev_workflow.py test --coverage

# Verbose output
./scripts/pt scripts/dev_workflow.py test -v
```

#### Run Linters
```bash
./scripts/pt scripts/dev_workflow.py lint
```
- Runs ruff for linting
- Runs black for formatting checks

#### Performance Check
```bash
./scripts/pt scripts/dev_workflow.py perf-check
```
- Benchmarks key operations
- Reports performance metrics
- Identifies slow operations

#### Validate Documentation
```bash
./scripts/pt scripts/dev_workflow.py docs-validate
```
- Checks for broken links
- Finds TODO/FIXME markers
- Validates file structure

#### Health Check
```bash
./scripts/pt scripts/dev_workflow.py health
```
- Verifies environment setup
- Checks directory structure
- Validates git status

#### Create Strategy Scaffold
```bash
./scripts/pt scripts/dev_workflow.py create-strategy "My New Strategy"
```
- Generates strategy boilerplate
- Creates test file template
- Provides next steps

---

## Workflow Patterns

### Pattern 1: Test-Driven Development (TDD)

```bash
# 1. Create test first
./scripts/pt scripts/dev_workflow.py create-strategy "momentum"
# Edit tests/strategies/test_momentum.py

# 2. Run test (should fail)
./scripts/pt scripts/dev_workflow.py test --module strategies/test_momentum -v

# 3. Implement strategy
# Edit src/strategies/momentum.py

# 4. Run test (should pass)
./scripts/pt scripts/dev_workflow.py test --module strategies/test_momentum -v

# 5. Refine and repeat
```

### Pattern 2: Performance-First Development

```bash
# 1. Baseline performance
./scripts/pt scripts/dev_workflow.py perf-check

# 2. Make changes
# ... edit files ...

# 3. Check performance impact
./scripts/pt scripts/dev_workflow.py perf-check

# 4. Compare metrics
# If performance degraded, optimize before committing
```

### Pattern 3: Documentation-Driven Development

```bash
# 1. Write documentation first
# Edit docs/YOUR_FEATURE.md

# 2. Validate documentation
./scripts/pt scripts/dev_workflow.py docs-validate

# 3. Implement based on docs
# ... edit files ...

# 4. Ensure docs stay updated
./scripts/pt scripts/dev_workflow.py docs-validate
```

### Pattern 4: Incremental Integration

```bash
# 1. Make small change
# Edit single file

# 2. Test immediately
./scripts/pt scripts/dev_workflow.py test --module <specific_test>

# 3. Commit if passes
git add <file>
git commit -m "Small incremental change"

# 4. Repeat for next small change
```

---

## IDE Integration

### VS Code Setup

Create `.vscode&#47;tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "./scripts/pt scripts/dev_workflow.py test",
            "group": {
                "kind": "test",
                "isDefault": true
            }
        },
        {
            "label": "Run Linters",
            "type": "shell",
            "command": "./scripts/pt scripts/dev_workflow.py lint",
            "group": "build"
        },
        {
            "label": "Health Check",
            "type": "shell",
            "command": "./scripts/pt scripts/dev_workflow.py health"
        }
    ]
}
```

Keyboard shortcuts:
- `Cmd+Shift+T`: Run tests
- `Cmd+Shift+B`: Run linters

### PyCharm Setup

1. **External Tools Configuration:**
   - Settings → Tools → External Tools
   - Add tool: "Workflow Health"
   - Program: `./scripts/pt`
   - Arguments: `scripts&#47;dev_workflow.py health`
   - Working directory: `$ProjectFileDir$`

2. **Run Configurations:**
   - Add Python configuration
   - Script: `scripts/dev_workflow.py`
   - Parameters: `test --module $Prompt$`

---

## Git Workflows

### Branch Naming Convention

```
feature/<feature-name>      # New feature
fix/<bug-description>       # Bug fix
refactor/<component>        # Code refactoring
docs/<topic>                # Documentation update
test/<area>                 # Test improvements
perf/<optimization>         # Performance improvement
```

### Commit Message Convention

```
type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- test: Test improvements
- refactor: Code refactoring
- perf: Performance improvement
- chore: Maintenance

Examples:
feat(strategies): add momentum strategy
fix(backtest): correct signal timing issue
docs(api): update performance monitoring guide
test(portfolio): add edge case tests
```

### Pull Request Workflow

1. **Before Creating PR:**
   ```bash
   ./scripts/pt scripts/dev_workflow.py test --coverage
   ./scripts/pt scripts/dev_workflow.py lint
   ./scripts/pt scripts/dev_workflow.py docs-validate
   ./scripts/pt scripts/dev_workflow.py health
   ```

2. **PR Description Template:**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Tests pass
   - [ ] Coverage maintained/improved
   - [ ] Manual testing performed

   ## Documentation
   - [ ] Documentation updated
   - [ ] Examples added

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] No safety issues introduced
   ```

---

## Testing Workflows

### Test Hierarchy

```
Unit Tests        → Fast, isolated, mocked
Integration Tests → Medium speed, real components
Smoke Tests       → Quick end-to-end validation
Full Suite        → Comprehensive, all tests
```

### Testing Strategy

```bash
# During development (fast feedback)
./scripts/pt scripts/dev_workflow.py test --module <your_module>

# Before commit (medium confidence)
./scripts/pt scripts/dev_workflow.py test --module <affected_modules>

# Before PR (high confidence)
./scripts/pt scripts/dev_workflow.py test --coverage

# CI/CD (full validation)
./scripts/pt -m pytest tests/ -v --cov=src --cov-report=html
```

### Test-Specific Workflows

```bash
# Run specific test class
./scripts/pt -m pytest tests/test_performance.py::TestPerformanceMonitor -v

# Run specific test method
./scripts/pt -m pytest tests/test_performance.py::TestPerformanceMonitor::test_init -v

# Run tests matching pattern
./scripts/pt -m pytest tests/ -k "performance" -v

# Run with detailed output
./scripts/pt -m pytest tests/ -vv -s

# Run failed tests only
./scripts/pt -m pytest tests/ --lf

# Run tests in parallel (if pytest-xdist installed)
./scripts/pt -m pytest tests/ -n auto
```

---

## Debugging Workflows

### Debugging Strategy

1. **Reproduce the Issue:**
   ```bash
   ./scripts/pt scripts/dev_workflow.py test --module <failing_test> -v
   ```

2. **Add Debug Output:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Use Debugger:**
   ```bash
   # Run with debugger
   ./scripts/pt -m pdb scripts/<script_name>.py

   # Or in test
   ./scripts/pt -m pytest tests/test_module.py --pdb
   ```

4. **Performance Profiling:**
   ```python
   from src.core.performance import performance_monitor

   with performance_monitor.measure("operation"):
       # Your code here
       pass

   performance_monitor.print_summary()
   ```

---

## Performance Optimization Workflow

### Optimization Process

1. **Measure Baseline:**
   ```bash
   ./scripts/pt scripts/dev_workflow.py perf-check
   ```

2. **Profile Code:**
   ```python
   import cProfile
   import pstats

   profiler = cProfile.Profile()
   profiler.enable()

   # Your code here

   profiler.disable()
   stats = pstats.Stats(profiler)
   stats.sort_stats('cumulative')
   stats.print_stats(20)
   ```

3. **Identify Bottlenecks:**
   - Check performance monitor metrics
   - Review profiler output
   - Analyze algorithm complexity

4. **Optimize:**
   - Cache frequently accessed data
   - Use vectorized operations (numpy/pandas)
   - Reduce I/O operations
   - Parallelize independent operations

5. **Verify Improvement:**
   ```bash
   ./scripts/pt scripts/dev_workflow.py perf-check
   # Compare with baseline
   ```

---

## Automation Tips

### Pre-commit Hooks

Create `.git&#47;hooks&#47;pre-commit`:

```bash
#!/bin/bash

echo "Running pre-commit checks..."

# Run tests
./scripts/pt scripts/dev_workflow.py test
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

# Run linters
./scripts/pt scripts/dev_workflow.py lint
if [ $? -ne 0 ]; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

echo "Pre-commit checks passed!"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

### Git Aliases

Add to `.gitconfig`:

```ini
[alias]
    pt-test = !./scripts/pt scripts/dev_workflow.py test
    pt-lint = !./scripts/pt scripts/dev_workflow.py lint
    pt-health = !./scripts/pt scripts/dev_workflow.py health
    pt-perf = !./scripts/pt scripts/dev_workflow.py perf-check
```

Usage:
```bash
git pt-test
git pt-lint
git pt-health
```

---

## Continuous Integration

### CI Pipeline Structure

```
Trigger: Push/PR
    ↓
1. Setup (install deps)
    ↓
2. Lint (ruff, black)
    ↓
3. Test (pytest with coverage)
    ↓
4. Performance Check
    ↓
5. Documentation Validation
    ↓
Success/Failure
```

### Local CI Simulation

```bash
# Simulate CI pipeline locally
./scripts/pt scripts/dev_workflow.py setup
./scripts/pt scripts/dev_workflow.py lint
./scripts/pt scripts/dev_workflow.py test --coverage
./scripts/pt scripts/dev_workflow.py perf-check
./scripts/pt scripts/dev_workflow.py docs-validate
```

---

## Productivity Metrics

### Track Your Progress

```bash
# Lines of code changed
git diff --stat

# Test coverage
./scripts/pt scripts/dev_workflow.py test --coverage

# Performance improvements
./scripts/pt scripts/dev_workflow.py perf-check
# Compare with previous baseline

# Documentation completeness
./scripts/pt scripts/dev_workflow.py docs-validate
```

---

## Troubleshooting

### Common Issues

#### Tests Failing After Update
```bash
# Update dependencies
pip install -e ".[dev]" --upgrade

# Clear pytest cache
rm -rf .pytest_cache

# Run tests again
./scripts/pt scripts/dev_workflow.py test
```

#### Performance Regression
```bash
# Profile the slow operation
./scripts/pt -m cProfile -o profile.stats scripts/<script>.py

# Analyze profile
./scripts/pt -m pstats profile.stats
> sort cumulative
> stats 20
```

#### Import Errors
```bash
# Verify installation
pip list | grep peak_trade

# Reinstall in editable mode
pip install -e .

# Check Python path
./scripts/pt -c "import sys; print('\n'.join(sys.path))"
```

---

## Additional Resources

### Internal
- [Dev Setup](DEV_SETUP.md)
- [CLI Cheatsheet](CLI_CHEATSHEET.md)
- [AI Workflow Guide](ai/AI_WORKFLOW_GUIDE.md)
- [Knowledge Base Index](KNOWLEDGE_BASE_INDEX.md)

### Tools
- [pytest documentation](https://docs.pytest.org/)
- [ruff documentation](https://docs.astral.sh/ruff/)
- [black documentation](https://black.readthedocs.io/)

---

## Version History

| Date       | Version | Changes                              |
|------------|---------|--------------------------------------|
| 2025-12-19 | 1.0     | Initial workflow guide created       |

---

**Navigation:** [⬆️ Back to Top](#peak_trade-developer-workflow-guide) | [📚 Knowledge Base](KNOWLEDGE_BASE_INDEX.md)
