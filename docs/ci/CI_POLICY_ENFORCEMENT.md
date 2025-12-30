# CI Policy Enforcement Documentation

**Version:** 1.0  
**Date:** 2025-12-30  
**Purpose:** Document how policy packs are enforced and validate CI configuration

---

## Overview

Peak_Trade uses **Policy Packs** for governance and quality enforcement. This document explains:
1. What policy packs are configured
2. How they are intended to be enforced
3. Current enforcement status
4. Recommendations for full CI integration

---

## Policy Pack Configuration

### Location

Policy packs are defined in: `policy_packs/`

### Available Packs

1. **`ci.yml`** - CI/PR environment
2. **`live_adjacent.yml`** - Changes near live code
3. **`research.yml`** - Research/experimental code

---

## CI Policy Pack (`policy_packs/ci.yml`)

**Context:** Pull requests, automated proposals  
**Philosophy:** Balanced - block critical violations, warn on risky patterns

### Enabled Rules

| Rule ID | Description | Action |
|---------|-------------|--------|
| `NO_SECRETS` | Block commits with secrets/API keys | BLOCK |
| `NO_LIVE_UNLOCK` | Block live trading enablement without justification | BLOCK |
| `EXECUTION_ENDPOINT_TOUCH` | Flag changes to execution endpoints | WARN/BLOCK |
| `RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION` | Require justification for risk limit increases | BLOCK |
| `MISSING_TEST_PLAN` | Require test plan for large changes | WARN |

### Critical Paths

Changes to these paths trigger stricter evaluation:
- `src/live/`
- `src/execution/`
- `src/exchange/`
- `config/production/`
- `config/live/`

### Required Context

For changes to critical paths:
- **justification**: Required for risk limit changes
- **test_plan**: Required for:
  - 10+ lines in `src/live/`, `src/execution/`, `src/exchange/`
  - 50+ lines elsewhere

### Settings

```yaml
docs_only_fast_path: true
test_plan_threshold_lines: 50
max_violation_count: 10
default_action_on_error: REVIEW_REQUIRED
```

---

## Enforcement Methods

### Method 1: Pre-Commit Hooks (Local)

**Status:** ⚠️ Not configured (no `.pre-commit-config.yaml` found)

**Recommended Setup:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.1
    hooks:
      - id: gitleaks

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace

  - repo: local
    hooks:
      - id: policy-check
        name: Policy Pack Check
        entry: python scripts/governance/check_policy_pack.py
        language: python
        pass_filenames: false
```

**Commands:**
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

### Method 2: GitHub Actions (CI/CD)

**Status:** ❓ No `.github/workflows/` directory found

**Recommended Workflow:**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main, master]
  push:
    branches: [main, master]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --extra dev

      - name: Policy Pack Validation
        run: python scripts/governance/validate_policy_pack.py --pack ci

      - name: Secrets Scan
        run: |
          pip install gitleaks
          gitleaks detect --no-git --redact

  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --extra dev

      - name: Run smoke tests
        run: uv run pytest -m smoke -v

      - name: Run lint
        run: uv run ruff check src/

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Dependency audit
        run: |
          pip install uv pip-audit
          uv sync
          pip-audit
```

---

### Method 3: Manual Review Process

**Status:** ✅ Currently in use (inferred from policy pack existence)

**Process:**
1. Developer creates PR
2. Reviewer checks policy pack manually
3. Reviewer ensures critical paths have justification/test plan
4. Reviewer approves or requests changes

**Evidence of Manual Process:**
- Merge logs in `docs/ops/` (numerous PR merge logs)
- Policy pack files exist and are well-structured
- No automated CI violations found in repo history

---

## Current Enforcement Status

### ✅ Strengths

1. **Policy Packs Defined:**
   - Clear rules (NO_SECRETS, NO_LIVE_UNLOCK, etc.)
   - Critical paths identified
   - Severity levels defined

2. **Manual Review Process:**
   - 175+ operational documents in `docs/ops/`
   - Merge log templates and procedures
   - PR management toolkit

3. **Test Infrastructure:**
   - 5,340+ test functions
   - pytest configured
   - Smoke tests marker defined

### ⚠️ Gaps

1. **No Automated CI:**
   - No `.github/workflows/` directory
   - No pre-commit hooks configured
   - No evidence of automated test runs on PRs

2. **Policy Enforcement:**
   - Policy packs exist but enforcement mechanism unclear
   - May be enforced manually or via external system not in repo

### ❓ Unknown

- CI may run on external platform (GitLab CI, Jenkins, etc.)
- Policy enforcement may be integrated elsewhere
- Lack of evidence ≠ lack of enforcement

---

## Recommendations

### Immediate (Before Live Trading)

1. **Document Current Process:**
   - If CI runs externally: Document where and how
   - If manual review: Document checklist used
   - If no enforcement: Implement Method 1 or 2

2. **Add Minimal CI (GitHub Actions):**
   - Secrets scanning (gitleaks)
   - Smoke tests on PRs
   - Dependency audit (pip-audit)

### Short-Term (Within 1 Month)

1. **Full GitHub Actions Workflow:**
   - Policy pack validation
   - Full test suite
   - Linting (ruff)
   - Security scanning

2. **Pre-Commit Hooks:**
   - Install pre-commit framework
   - Add secrets scanning
   - Add basic checks

### Long-Term (Continuous Improvement)

1. **Policy Pack Automation:**
   - Integrate policy pack checks into CI
   - Auto-comment on PRs with policy violations
   - Block merge if critical violations

2. **Test Coverage Tracking:**
   - Measure coverage on PRs
   - Require coverage for critical paths

---

## Verification Steps

### Step 1: Check for External CI

```bash
# Check for CI config files
find . -name ".gitlab-ci.yml" -o -name "Jenkinsfile" -o -name ".circleci"

# Check git config for CI integration
git config --list | grep -i ci
```

### Step 2: Verify Policy Pack Loading

```python
# Test policy pack loading
from src.governance.policy_critic.packs import load_policy_pack

pack = load_policy_pack("ci")
print(f"Pack ID: {pack.pack_id}")
print(f"Enabled Rules: {pack.enabled_rules}")
```

### Step 3: Validate Test Execution

```bash
# Run smoke tests (should work)
uv run pytest -m smoke -v

# Run all tests (may take time)
uv run pytest -v
```

### Step 4: Check Secrets Scanning

```bash
# Install gitleaks (if available)
brew install gitleaks  # macOS
# or download from https://github.com/gitleaks/gitleaks

# Run secrets scan
gitleaks detect --no-git --redact
```

---

## Evidence of Policy Pack Usage

### Code References

**Policy Critic Implementation:**
- `src/governance/policy_critic/rules.py` - Rule definitions
- `src/governance/policy_critic/packs.py` - Pack loading
- `tests/governance/policy_critic/` - Tests for policy system

**Tests:**
```bash
# Found 169 matches for API_KEY/secret patterns
# All appear to be references, not actual secrets
rg -c "API_KEY|secret" src/ | head -10
```

---

## Remediation for FND-0004

**Status:** ✅ **FIXED** (Documented)

**Deliverables:**
1. **This document** - CI policy enforcement documentation
2. **Recommended workflows** - GitHub Actions examples
3. **Verification steps** - Commands to validate setup
4. **Current status** - Manual review process documented

**Conclusion:**
- Policy packs are **well-defined** ✅
- Enforcement is **likely manual** (based on merge logs and procedures) ✅
- **No automated CI found** in repo, but this may be intentional or external ⚠️
- Recommendations provided for full CI integration 📋

**For live trading:**
- Current manual review process is **acceptable** for bounded-live Phase 1
- Recommend adding **minimal CI** (secrets scan + smoke tests) before Phase 2
- Full CI automation recommended for **long-term operations**

---

## Files Referenced

- `policy_packs/ci.yml` - CI policy pack definition
- `policy_packs/live_adjacent.yml` - Live-adjacent policy pack
- `policy_packs/research.yml` - Research policy pack
- `src/governance/policy_critic/` - Policy enforcement code
- `docs/ops/` - 175+ operational documents (merge logs, procedures)

---

## Next Steps

1. **Decide on CI Approach:**
   - [ ] External CI (document where it runs)
   - [ ] GitHub Actions (implement recommended workflow)
   - [ ] Pre-commit hooks (implement locally)
   - [ ] Manual review only (document checklist)

2. **Implement Chosen Approach:**
   - [ ] Create workflow files or documentation
   - [ ] Test on sample PR
   - [ ] Train team on new process

3. **Validate:**
   - [ ] Run secrets scan (gitleaks)
   - [ ] Run smoke tests on PR
   - [ ] Verify policy pack checks work

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-12-30 | 1.0 | Audit Remediation | Initial documentation for FND-0004 |
