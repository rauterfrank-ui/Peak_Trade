# CI/CD Architecture

Complete overview of Peak Trade's CI/CD pipeline, automation workflows, and quality gates.

## Overview

Peak Trade uses GitHub Actions for continuous integration and deployment with the following goals:

- ✅ **Fast Feedback** - Quick feedback on code quality (<10 minutes)
- ✅ **High Quality** - Automated quality gates prevent bad code
- ✅ **Safe Deployment** - Gradual rollouts with feature flags
- ✅ **Developer Experience** - Easy local development and testing

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Developer Workflow                       │
├─────────────────────────────────────────────────────────────┤
│  1. Code Changes                                             │
│  2. Pre-commit Hooks  ──► Ruff, MyPy, Bandit                │
│  3. Local Testing     ──► make ci-local                      │
│  4. Push to GitHub                                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions (CI)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Quality    │  │     Main     │  │     Docs     │     │
│  │   Workflow   │  │   CI Tests   │  │  Generation  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  • Lint (Ruff)     • Tests (3.10-12)  • Build Docs        │
│  • Type Check      • Linux + macOS    • Validate Links     │
│  • Security Scan   • Strategy Smoke   • Generate API       │
│  • Test Coverage   • RL Validation                         │
│                                                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ (All checks pass)
┌─────────────────────────────────────────────────────────────┐
│                   Deployment & Release                       │
├─────────────────────────────────────────────────────────────┤
│  • Feature Flags Control Rollouts                           │
│  • Gradual Deployment (10% → 50% → 100%)                   │
│  • Monitoring & Alerts                                       │
│  • Instant Rollback via Flags                               │
└─────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. Quality Workflow (`quality.yml`)

**Purpose:** Enforce code quality standards

**Triggers:**
- Push to `main`, `master`, `develop`
- Pull requests to these branches
- Manual workflow dispatch

**Jobs:**

#### Lint & Format Check
```yaml
- Ruff linting (comprehensive rule set)
- Ruff formatting check
- Import sorting validation
```

#### Type Check
```yaml
- MyPy static type analysis
- Type coverage reporting
- Advisory mode (non-blocking for gradual adoption)
```

#### Security Scan
```yaml
- Bandit: Python security linter
- Safety: Dependency vulnerability check
- pip-audit: PyPI package auditor
```

#### Test Coverage (Matrix)
```yaml
Python Versions: [3.10, 3.11, 3.12]
- pytest with coverage
- Coverage reports (XML, HTML, term)
- 40% coverage threshold (gradually increasing to 80%)
```

**Artifacts:**
- Coverage reports (XML, HTML)
- Security scan results (JSON)

**Runtime:** ~8-12 minutes

---

### 2. Main CI Workflow (`ci.yml`)

**Purpose:** Core integration testing

**Triggers:**
- Push to `main`, `master`
- Pull requests
- Weekly schedule (Monday 03:00 UTC)
- Manual dispatch

**Jobs:**

#### Tests (Matrix)
```yaml
OS: [ubuntu-latest, macos-latest]
Python: [3.10, 3.11, 3.12] (full matrix on main/schedule)
Python: [3.11] (PR quick validation)
```

**Test Categories:**
- Unit tests
- Integration tests
- RL v0.1 contract validation
- Strategy smoke tests

**Caching:**
- pip packages (~500MB)
- pytest cache
- Platform-specific paths (Linux/macOS)

**Artifacts:**
- Test reports
- Coverage XML
- RL validation reports (on failure)
- Strategy smoke results

**Runtime:** ~5-8 minutes (PR), ~15-20 minutes (full matrix)

---

### 3. Documentation Workflow (`docs.yml`)

**Purpose:** Validate and build documentation

**Triggers:**
- Push to `main`, `master`
- Pull requests
- Manual dispatch

**Jobs:**

#### Build Docs
```yaml
- Check documentation structure
- Validate markdown files
- Check for broken links
- Generate API documentation index
- Upload documentation artifacts
```

**Future Enhancements:**
- Sphinx documentation build
- Deploy to GitHub Pages
- API documentation auto-generation

**Runtime:** ~2-3 minutes

---

### 4. Dependency Update Workflow (`dependency-update.yml`)

**Purpose:** Automated dependency monitoring

**Triggers:**
- Weekly schedule (Monday 00:00 UTC)
- Manual dispatch

**Jobs:**

#### Check Updates
```yaml
- List outdated packages
- Run security audit (pip-audit)
- Generate update report
- Upload report as artifact
```

**Future Enhancements:**
- Auto-create PRs with updates
- Automated testing of updated dependencies
- Slack/Discord notifications

**Runtime:** ~3-5 minutes

---

## Quality Gates

### Pre-commit (Local)

**Enforced by pre-commit hooks:**
1. Ruff linting with auto-fix
2. Ruff formatting
3. MyPy type checking
4. Bandit security scanning
5. File formatting checks (trailing whitespace, EOF, YAML)

**Skip when necessary:**
```bash
git commit --no-verify  # Use sparingly!
```

### Pull Request Gates

**Must pass before merge:**
1. ✅ All quality checks (lint, type, security)
2. ✅ All tests pass on primary Python version
3. ✅ Coverage meets threshold
4. ✅ No security vulnerabilities introduced
5. ✅ Documentation updated (if needed)
6. ✅ At least one reviewer approval

**Optional (advisory):**
- Type checking (gradual adoption)
- Full matrix tests (run on main)
- macOS compatibility

### Merge Requirements

**Protected branch rules:**
- Require PR approval
- Require status checks to pass
- Require conversation resolution
- No force pushes
- No branch deletion

---

## Local Development

### Setup

```bash
# Automated setup (macOS)
bash scripts/setup_macos.sh

# Activate environment
source venv/bin/activate

# Validate setup
make validate-env
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Quality Checks

```bash
# All quality checks (what CI runs)
make quality

# Individual checks
make lint          # Ruff linting
make lint-fix      # Auto-fix issues
make typecheck     # MyPy
make security      # Security scans
make test          # Run tests
make coverage      # Tests with coverage
```

### CI Simulation

Run complete CI pipeline locally:

```bash
make ci-local
```

This runs:
1. Clean build artifacts
2. Lint + type check + security scan
3. Tests with coverage
4. Documentation validation

**Expected time:** ~3-5 minutes

---

## Caching Strategy

### pip Cache

**Cached:**
- `~/.cache/pip` (Linux)
- `~/Library/Caches/pip` (macOS)

**Cache Key:**
```yaml
${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt') }}
```

**Benefits:**
- ~2-3 minutes faster per run
- Reduced network usage
- More reliable builds

### pytest Cache

**Cached:**
- `.pytest_cache/`

**Cache Key:**
```yaml
${{ runner.os }}-pytest-${{ matrix.python-version }}-${{ hashFiles('tests/**/*.py') }}
```

**Benefits:**
- Faster test discovery
- Reuses test order optimization

---

## Artifact Management

### Coverage Reports

**Uploaded artifacts:**
- `coverage.xml` - For external tools (Codecov, etc.)
- `htmlcov/` - Interactive HTML report
- Retention: 30 days

### Test Reports

**Uploaded artifacts:**
- Test results (JSON/XML)
- pytest cache
- Strategy smoke results
- Retention: 30 days

### Security Reports

**Uploaded artifacts:**
- Bandit findings (JSON)
- Safety reports
- pip-audit results
- Retention: 30 days

### Documentation

**Uploaded artifacts:**
- Built documentation
- API docs
- Retention: 30 days

---

## Performance Optimization

### Matrix Strategy

**Pull Requests:**
- Single Python version (3.11)
- Linux only
- **Goal:** <5 minutes

**Main Branch:**
- Multiple Python versions (3.10, 3.11, 3.12)
- Multiple OS (Linux, macOS)
- **Goal:** <15 minutes

### Parallel Execution

**Tests:**
```yaml
pytest -n auto  # Use all CPU cores
```

**Workflows:**
- Jobs run in parallel
- Matrix builds run concurrently
- Independent artifact uploads

### Fail-Fast Strategy

```yaml
strategy:
  fail-fast: false  # Continue other jobs if one fails
```

**Benefits:**
- See all failures, not just first
- Better debugging information
- Complete test coverage report

---

## Monitoring & Alerts

### GitHub Status Checks

**Visible on PRs:**
- ✅ All checks passed
- ❌ Check failed (with details)
- 🟡 Check in progress

**Click for details:**
- Full workflow logs
- Test failures
- Coverage reports
- Security findings

### Notifications

**Current:**
- GitHub UI notifications
- Email (configurable)

**Future:**
- Slack webhook integration
- Discord notifications
- Custom alerting rules

---

## Security

### Secret Management

**Stored in GitHub Secrets:**
- API keys (encrypted)
- Authentication tokens
- Webhook URLs

**Never commit:**
- API keys
- Passwords
- Private keys
- `.env` files

### Dependency Security

**Automated scanning:**
- `safety check` - Known vulnerabilities
- `pip-audit` - PyPI advisory database
- `bandit` - Code security issues

**Weekly checks:**
- Dependency update workflow
- Vulnerability reports
- Auto-generated update recommendations

### Code Security

**Bandit rules:**
- SQL injection detection
- Hardcoded secrets
- Insecure functions
- Shell injection
- Assert usage

---

## Troubleshooting

### CI Fails Locally Passes

**Check Python version:**
```bash
python --version  # Should match CI (3.10-3.12)
```

**Clean and retry:**
```bash
make clean
make ci-local
```

**Check environment:**
```bash
make validate-env
```

### Slow CI Runs

**Check cache:**
- Verify cache is being used
- Check cache hit rate in logs

**Optimize tests:**
```bash
pytest --durations=10  # Find slow tests
```

**Use markers:**
```python
@pytest.mark.slow  # Mark slow tests
pytest -m "not slow"  # Skip in CI
```

### Flaky Tests

**Identify:**
```bash
pytest --count=10  # Run tests multiple times
```

**Fix:**
- Add proper setup/teardown
- Use fixtures correctly
- Avoid timing dependencies
- Mock external services

---

## Best Practices

### 1. Run CI Locally First

```bash
make ci-local  # Before pushing
```

### 2. Write Fast Tests

- Unit tests < 100ms each
- Mark slow tests with `@pytest.mark.slow`
- Use mocks for external services

### 3. Keep Workflows Simple

- One clear purpose per workflow
- Reusable actions
- Clear job names

### 4. Monitor Performance

- Track workflow durations
- Optimize slow jobs
- Use caching effectively

### 5. Document Changes

- Update this doc when changing workflows
- Add comments to workflow files
- Link to issues for context

---

## Future Enhancements

### Planned

- [ ] Codecov integration
- [ ] GitHub Pages deployment
- [ ] Automated PR creation for dependency updates
- [ ] Performance regression testing
- [ ] Load testing integration
- [ ] Canary deployments

### Under Consideration

- [ ] Multi-stage deployments
- [ ] Blue-green deployment
- [ ] Automated rollback on errors
- [ ] Chaos engineering tests
- [ ] A/B test framework integration

---

## Related Documentation

- [Contributing Guide](../guides/contributing.md)
- [Feature Flags](../guides/feature-flags.md)
- [macOS Setup](../guides/macos-setup.md)
- [Strategy Development](../STRATEGY_DEV_GUIDE.md)

---

**Questions?** Open an issue or discussion on GitHub.

**Last Updated:** December 2024
