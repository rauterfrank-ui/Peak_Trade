# CI/CD Architecture - Peak_Trade

## Overview

Peak_Trade uses a **3-Tier CI/CD Pipeline Architecture** designed for fast feedback, comprehensive validation, and security-first development.

### Design Principles

1. **Fast Feedback First**: Critical checks complete in under 5 minutes
2. **Parallel Execution**: Tests run concurrently across multiple Python versions
3. **Security First**: Automated security scanning for dependencies and secrets
4. **Clear Separation**: Unit, integration, and smoke tests run independently
5. **Comprehensive Coverage**: Code coverage tracking and reporting

---

## 3-Tier System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TIER 1: Fast Gates                       │
│                        (< 5 min)                            │
├─────────────────────────────────────────────────────────────┤
│  • lint.yml         - Code quality & formatting             │
│  • security.yml     - Security scanning                     │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                   TIER 2: Core CI                           │
│                       (< 15 min)                            │
├─────────────────────────────────────────────────────────────┤
│  • ci-unit.yml           - Unit tests (3.10, 3.11, 3.12)   │
│  • ci-integration.yml    - Integration tests & RL contract  │
│  • ci-strategy-smoke.yml - Strategy smoke tests             │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                TIER 3: Deep Validation                      │
│                       (< 20 min)                            │
├─────────────────────────────────────────────────────────────┤
│  • audit.yml        - PR report validation & audit          │
│  • offline_suites.yml - Offline test suites                │
│  • policy_critic.yml - Policy validation                    │
│  • test_health.yml   - Test health monitoring               │
└─────────────────────────────────────────────────────────────┘
```

---

## Workflow Details

### TIER 1: Fast Gates (< 5 min)

#### `lint.yml` - Code Quality & Formatting
**Purpose**: Catch code quality issues early  
**Triggers**: PR, push to main, manual  
**Jobs**:
- Ruff linting (src/, tests/, scripts/)
- Black formatting check
- isort import sorting check
- mypy type checking (optional, non-blocking)

**Key Features**:
- Concurrency control (cancels old runs)
- Pip caching for faster execution
- GitHub annotations for lint errors
- 5-minute timeout

**Permissions**: `contents:read`, `pull-requests:write`

---

#### `security.yml` - Security Scanning
**Purpose**: Detect vulnerabilities and secrets  
**Triggers**: PR, push to main, schedule (Monday 04:00), manual  
**Jobs**:
1. **dependency-scan**:
   - Safety check (dependency vulnerabilities)
   - Bandit (Python security linter)
   - JSON reports as artifacts (30 days)

2. **secret-scan**:
   - TruffleHog secret scanning
   - Full git history scan

**Key Features**:
- Automated weekly scans
- Security reports uploaded as artifacts
- Non-blocking by default (continue-on-error)
- 10-minute timeout

**Permissions**: `contents:read`, `security-events:write`, `actions:read`

---

### TIER 2: Core CI (< 15 min)

#### `ci-unit.yml` - Unit Tests
**Purpose**: Fast unit test execution across Python versions  
**Triggers**: PR, push to main, schedule (Monday 03:00), manual  
**Jobs**:
- Python matrix: 3.10, 3.11, 3.12
- Parallel test execution (pytest-xdist: `-n auto`)
- Test marker: `-m "not integration and not slow"`
- Coverage (Python 3.11 only):
  - XML, HTML, Terminal reports
  - Codecov upload (non-blocking)
- JUnit XML results

**Key Features**:
- Concurrent test execution
- Per-version pip caching
- Coverage reports uploaded to Codecov
- 15-minute timeout

**Permissions**: `contents:read`, `checks:write`, `pull-requests:write`

---

#### `ci-integration.yml` - Integration Tests
**Purpose**: Integration tests and RL contract validation  
**Triggers**: PR, push to main, manual  
**Jobs**:
- Python 3.11 only
- RL v0.1 Contract Smoke Test
- RL v0.1 Contract Validation (bash script)
- Integration tests: `-m "integration"`
- Upload validation reports on failure (7 days)

**Key Features**:
- RL contract validation
- Detailed failure reports
- 20-minute timeout

**Permissions**: `contents:read`, `checks:write`

---

#### `ci-strategy-smoke.yml` - Strategy Smoke Tests
**Purpose**: Validate all strategies pass basic checks  
**Triggers**: PR, push to main, manual  
**Jobs**:
- Python 3.11 only
- Strategy smoke pytest
- Strategy smoke CLI execution
- Results uploaded as artifacts (30 days)

**Key Features**:
- Offline-only (no live/testnet)
- CLI and pytest validation
- 10-minute timeout

**Permissions**: `contents:read`, `checks:write`

---

### TIER 3: Deep Validation

#### `audit.yml` - Audit Checks (Optimized)
**Purpose**: PR report validation and comprehensive audit  
**Triggers**: PR, push to main, schedule (Monday 06:00), manual  
**Jobs**:
- PR report format validation
- Comprehensive repository audit
- Artifacts uploaded on completion

**Improvements**:
- Added explicit permissions
- Added pip caching
- Reduced timeout from 20 to 15 minutes
- Better job descriptions

**Permissions**: `contents:read`, `checks:write`, `pull-requests:write`

---

## Data Flow Diagram

```
┌─────────────┐
│   PR/Push   │
└──────┬──────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌─────────────┐                      ┌─────────────┐
│  Lint Check │                      │  Security   │
│  (TIER 1)   │                      │  (TIER 1)   │
└──────┬──────┘                      └──────┬──────┘
       │                                     │
       └───────────────┬─────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Unit Tests │ │ Integration │ │  Strategy   │
│  (TIER 2)   │ │  (TIER 2)   │ │   Smoke     │
│             │ │             │ │  (TIER 2)   │
│ 3.10  3.11  │ │    3.11     │ │    3.11     │
│      3.12   │ │             │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
                       ▼
                ┌─────────────┐
                │    Audit    │
                │  (TIER 3)   │
                └──────┬──────┘
                       │
                       ▼
                  ✅ All Pass
```

---

## Workflow Matrix

| Workflow | Trigger | Python | Timeout | Dependencies | Artifacts |
|----------|---------|--------|---------|--------------|-----------|
| **lint.yml** | PR, push, manual | 3.11 | 5 min | ruff, black, isort, mypy | - |
| **security.yml** | PR, push, schedule, manual | 3.11 | 10 min | safety, bandit, trufflehog | security reports (30d) |
| **ci-unit.yml** | PR, push, schedule, manual | 3.10, 3.11, 3.12 | 15 min | pytest, pytest-cov, pytest-xdist | coverage, test results (30d) |
| **ci-integration.yml** | PR, push, manual | 3.11 | 20 min | pytest | RL validation reports (7d) |
| **ci-strategy-smoke.yml** | PR, push, manual | 3.11 | 10 min | pytest | smoke results (30d) |
| **audit.yml** | PR, push, schedule, manual | 3.11 | 15 min | requirements.txt | audit artifacts |

---

## Cache Strategy

### Basic Cache (Single Version)
```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt', '**/pyproject.toml') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### Enhanced Cache (Per Python Version)
```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/requirements.txt', '**/pyproject.toml') }}
    restore-keys: |
      ${{ runner.os }}-pip-${{ matrix.python-version }}-
      ${{ runner.os }}-pip-
```

### Workflow-Specific Cache
```yaml
key: ${{ runner.os }}-pip-lint-${{ hashFiles('**/requirements.txt', '**/pyproject.toml') }}
```

---

## Concurrency Control

All PR workflows use concurrency groups to automatically cancel outdated runs:

```yaml
concurrency:
  group: ci-unit-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

**Benefits**:
- Saves CI/CD resources
- Faster feedback on latest changes
- Prevents confusion from old runs

---

## Codecov Integration

Coverage data is collected from unit tests (Python 3.11 only) and uploaded to Codecov:

```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    flags: unittests
    name: codecov-unit-tests
    fail_ci_if_error: false
```

**Setup Requirements**:
1. Add `CODECOV_TOKEN` to repository secrets
2. Configure Codecov project settings
3. Enable Codecov GitHub integration

---

## Troubleshooting Guide

### Common Issues

#### Lint Failures
**Symptom**: Ruff, Black, or isort checks fail  
**Solution**:
1. Run locally: `ruff check src/ tests/ scripts/ --fix`
2. Run locally: `black src/ tests/ scripts/`
3. Run locally: `isort src/ tests/ scripts/ --profile black`
4. Or use pre-commit: `pre-commit run --all-files`

#### Security Scan Failures
**Symptom**: Safety or Bandit report vulnerabilities  
**Solution**:
1. Review the security reports in workflow artifacts
2. Update vulnerable dependencies: `pip install --upgrade <package>`
3. If false positive, add to ignore list in workflow
4. For secrets, remove from git history using BFG or git-filter-repo

#### Test Failures
**Symptom**: Unit or integration tests fail  
**Solution**:
1. Check test logs in workflow details
2. Run locally: `pytest tests/ -v`
3. For integration tests: `pytest tests/ -m integration -v`
4. For unit tests only: `pytest tests/ -m "not integration and not slow" -v`

#### Coverage Issues
**Symptom**: Codecov upload fails or coverage too low  
**Solution**:
1. Ensure `CODECOV_TOKEN` secret is set
2. Check coverage locally: `pytest --cov=src --cov-report=term-missing`
3. Codecov failures are non-blocking by default

#### Cache Issues
**Symptom**: Slow workflows even with caching  
**Solution**:
1. Check cache hit rates in workflow logs
2. Clear cache: Settings → Actions → Caches → Delete
3. Verify cache keys include all relevant files

---

## Best Practices

### For Developers

1. **Run pre-commit hooks**: Install and use pre-commit hooks locally
   ```bash
   pip install pre-commit
   pre-commit install
   pre-commit run --all-files
   ```

2. **Test before pushing**: Run tests locally to catch issues early
   ```bash
   pytest tests/ -m "not integration and not slow"
   ```

3. **Check coverage**: Ensure new code is tested
   ```bash
   pytest --cov=src --cov-report=term-missing
   ```

4. **Monitor CI status**: Watch for failures and fix promptly

### For Reviewers

1. **Wait for CI**: Don't approve until all checks pass
2. **Review coverage**: Check if new code has adequate tests
3. **Check security**: Review security scan results in artifacts
4. **Verify docs**: Ensure changes are documented

---

## Migration from Old CI

The old `ci.yml` workflow has been replaced with the 3-tier architecture:

| Old ci.yml Job | New Workflow | Notes |
|----------------|--------------|-------|
| `tests` | `ci-unit.yml` | Now with Python matrix |
| `strategy-smoke` | `ci-strategy-smoke.yml` | Extracted as standalone |
| Linting (commented) | `lint.yml` | Now active and enforced |
| N/A | `security.yml` | New security scanning |
| N/A | `ci-integration.yml` | Separated from unit tests |

**Benefits of Migration**:
- Faster feedback (parallel execution)
- Better separation of concerns
- More comprehensive testing
- Security scanning included
- Easier to debug failures

---

## Future Enhancements

### Planned (TODO_PIPELINE_BOARD.md)

- [ ] OS matrix expansion (Ubuntu/macOS/Windows)
- [ ] Docker build tests
- [ ] Performance benchmarking
- [ ] Deployment pipeline (if needed)
- [ ] Advanced caching strategies
- [ ] Workflow dispatch with custom parameters

### Under Consideration

- [ ] Merge queue integration
- [ ] Custom GitHub Actions (composite actions)
- [ ] Self-hosted runners (for heavy workloads)
- [ ] Nightly comprehensive test runs
- [ ] Slack/Discord notifications

---

## Related Documentation

- [Branch Protection Rules](BRANCH_PROTECTION_RULES.md)
- [TODO Pipeline Board](TODO_PIPELINE_BOARD.md)
- [Test Health Automation](/docs/ops/TEST_HEALTH_AUTOMATION_V1.md)
- [CI Overview](/docs/ops/CI.md)

---

## Support

For questions or issues with CI/CD:
1. Check this documentation first
2. Review workflow logs in GitHub Actions tab
3. Check existing GitHub Issues
4. Create new issue with `ci` label
