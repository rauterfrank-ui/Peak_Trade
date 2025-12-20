# CI/CD Pipeline

Peak Trade uses GitHub Actions for continuous integration and deployment.

## Workflows

### 1. CI Pipeline (`.github/workflows/ci.yml`)

Runs on every push and pull request to `main`/`master`.

**Jobs**:

#### Lint Job
- Runs code quality checks
- Uses Ruff for fast linting
- Checks code formatting
- Runs MyPy type checking (non-blocking)
- Runs Bandit security scan (non-blocking)

```yaml
- Ruff lint
- Ruff format check
- MyPy type check
- Bandit security scan
```

#### Test Job
- Matrix testing across Python versions (3.9, 3.10, 3.11)
- Runs full test suite
- Generates coverage reports
- Uploads to Codecov

```yaml
- Python 3.9, 3.10, 3.11
- pytest with coverage
- Codecov upload
```

#### Strategy Smoke Tests
- Validates all strategies pass basic checks
- Offline testing only (no API keys required)
- Fast feedback on strategy health

### 2. Documentation Pipeline (`.github/workflows/docs.yml`)

Builds and deploys documentation on:
- Push to `main`/`master`
- Changes to `docs/**` or `mkdocs.yml`

**Steps**:
1. Install MkDocs and dependencies
2. Build documentation site
3. Deploy to GitHub Pages

**Access**: Documentation available at `https://rauterfrank-ui.github.io/Peak_Trade`

### 3. Deploy Pipeline (`.github/workflows/deploy.yml`)

Triggers on version tags (`v*`).

**Steps**:
1. Build Python package
2. Validate package with Twine
3. Build Docker image
4. Create GitHub Release with artifacts

## Pre-commit Hooks

Runs automatically on `git commit`:

```yaml
repos:
  - ruff (linting + formatting)
  - mypy (type checking)
  - bandit (security)
  - pre-commit-hooks:
    - trailing-whitespace
    - end-of-file-fixer
    - check-yaml
    - check-json
    - check-toml
    - check-merge-conflict
```

**Install**:
```bash
pre-commit install
```

**Run manually**:
```bash
pre-commit run --all-files
```

## Local Quality Checks

### Quick Check
```bash
# Run linting
ruff check .

# Run formatting
ruff format .

# Run type check
mypy src/

# Run security scan
bandit -r src/ -ll
```

### Comprehensive Check
```bash
# Run all checks
python scripts/code_review.py

# Or use Makefile
make check
```

### Test Coverage
```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Or use Makefile
make test-cov
```

## Makefile Targets

Convenient shortcuts for common tasks:

```bash
make test          # Run tests
make test-cov      # Run tests with coverage
make lint          # Run linting
make typecheck     # Run type checking
make security      # Run security scan
make check         # Run all quality checks
make format        # Format code
make docs          # Build documentation
make docs-serve    # Serve documentation locally
```

## Continuous Deployment

### Version Tagging

Create a new release:

```bash
# Tag a version
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

This triggers the deploy workflow:
1. Builds Python package
2. Creates Docker image
3. Publishes GitHub Release

### Manual Deployment

```bash
# Build package
python -m build

# Check package
twine check dist/*

# Upload to PyPI (if configured)
twine upload dist/*
```

## Monitoring CI/CD

### GitHub Actions Dashboard

View workflow runs:
- Go to repository → Actions tab
- View recent workflow runs
- Check logs for failures

### Status Badges

Add to README:

```markdown
![CI](https://github.com/rauterfrank-ui/Peak_Trade/workflows/CI/badge.svg)
![Docs](https://github.com/rauterfrank-ui/Peak_Trade/workflows/Documentation/badge.svg)
```

## Troubleshooting

### Pre-commit Fails

Update hooks:
```bash
pre-commit clean
pre-commit autoupdate
pre-commit install
```

### CI Tests Fail

Run locally:
```bash
# Run same tests as CI
pytest tests/ -v

# Check specific test
pytest tests/test_workflows.py -v
```

### Documentation Build Fails

Test locally:
```bash
# Install dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Build docs
mkdocs build

# Serve locally
mkdocs serve
```

## Best Practices

1. **Run checks locally** before pushing
2. **Keep CI fast** - optimize test suite
3. **Fix broken builds immediately**
4. **Monitor coverage trends**
5. **Update dependencies regularly**

## See Also

- [Contributing Guide](contributing.md)
- [Code Review Process](code-review.md)
- [Testing Guide](../guides/testing.md)
