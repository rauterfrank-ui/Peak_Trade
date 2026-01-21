# Build & Reproducibility Evidence

**Evidence ID:** EV-2001  
**Date:** 2025-12-30  
**Audit Baseline:** fb829340dbb764a75c975d5bf413a4edb5e47107

## Dependency Management

### Package Manager
- **Tool:** `uv` version 0.9.18 (2025-12-16)
- **Lockfile:** `uv.lock` (6,377 lines)
- **Status:** ✅ Lockfile present and substantial

### Python Version
- **Required:** `>=3.9` (from pyproject.toml)
- **Available:** Python 3.9.6
- **Status:** ✅ Meets minimum requirement

### Dependency Declaration
- **File:** `pyproject.toml`
- **Core Dependencies:**
  - numpy>=1.24.0
  - pandas>=2.0.0
  - pydantic>=2.0.0
  - toml>=0.10.2
  - ccxt>=4.0.0 (exchange integration)
  - pyarrow>=12.0.0
  - urllib3>=2.6.2,<3

- **Optional Dependencies:**
  - dev: pytest, ruff, black
  - web: fastapi, uvicorn, jinja2
  - viz: matplotlib
  - otel: OpenTelemetry stack
  - knowledge: chromadb
  - monitoring: prometheus-client

### Lockfile Analysis
- **Format:** UV lockfile v1, revision 3
- **Resolution Markers:** Python 3.9 through 3.14
- **Constraints:** onnxruntime==1.19.2 for Python <3.10
- **Status:** ✅ Comprehensive, version-pinned

## Test Infrastructure

### Test Framework
- **Tool:** pytest (configured in pytest.ini)
- **Test Files:** 276 test files
- **Test Functions:** 5,340+ test functions (across 278 files)
- **Status:** ⚠️ pytest not in PATH (may require `uv run pytest`)

### Test Configuration (pytest.ini)
- **Test Discovery:** `tests/` directory
- **Markers Defined:**
  - smoke: Fast CI tests (<10s)
  - slow: Long-running tests
  - integration: Integration tests
  - live: Live/testnet components
  - requires_api: External API tests
  - web: FastAPI/web stack tests
  - asyncio: Async tests

- **Warning Filters:**
  - Pandas FutureWarnings (fillna downcasting) - filtered
  - NumPy DeprecationWarnings - filtered
  - Pytest collection warnings - filtered
  - Default: Show all other warnings

### Test Coverage Breadth
- **Total Test Files:** 276
- **Key Test Areas:**
  - `tests/risk_layer/` - Risk layer tests (kill_switch, alerting, var_backtest)
  - `tests/risk/` - Legacy risk tests
  - `tests/execution/` - Execution pipeline tests
  - `tests/live/` - Live trading tests (via test_live_*.py)
  - `tests/strategies/` - Strategy tests
  - `tests/reporting/` - Reporting tests
  - `tests/trigger_training/` - Trigger training tests
  - `tests/governance/` - Governance tests

## CI/CD Policy Enforcement

### Policy Packs
Three policy packs defined in `policy_packs/`:

#### 1. CI Policy (`ci.yml`)
- **Context:** Pull requests, automated proposals
- **Philosophy:** Balanced - block critical, warn on risky
- **Enabled Rules:**
  - NO_SECRETS
  - NO_LIVE_UNLOCK
  - EXECUTION_ENDPOINT_TOUCH
  - RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION
  - MISSING_TEST_PLAN

- **Critical Paths:**
  - `src/live/`
  - `src/execution/`
  - `src/exchange/`
  - `config&#47;production&#47;`
  - `config&#47;live&#47;`

- **Required Context:**
  - justification (for risk limit changes)
  - test_plan (for changes to critical paths: 10+ lines in live/execution/exchange, 50+ elsewhere)

- **Settings:**
  - Docs-only fast path enabled
  - Test plan threshold: 50 lines
  - Max violations before auto-deny: 10

#### 2. Live Adjacent Policy (`live_adjacent.yml`)
- **Context:** Changes near live trading code
- **Philosophy:** Stricter than CI

#### 3. Research Policy (`research.yml`)
- **Context:** Research/experimental code
- **Philosophy:** More permissive

### Status
✅ Policy framework in place
✅ Critical paths identified
✅ Secrets scanning enforced
⚠️ No evidence of actual CI runs (no .github/workflows/ found)

## Linter Configuration

### Ruff (pyproject.toml)
- **Line Length:** 100
- **Target Version:** Python 3.9
- **Selected Rules:** E (pycodestyle errors), F (pyflakes)
- **Ignored Rules:**
  - E402 (module import not at top)
  - E501 (line too long)
  - E741 (ambiguous variable name)
  - F401 (imported but unused)
  - F811 (redefinition)
  - F821 (undefined name)
  - F841 (unused variable)

**Note:** Many rules ignored for "legacy code" compatibility

### Black (pyproject.toml)
- **Line Length:** 100
- **Target Versions:** Python 3.9, 3.10, 3.11

## Reproducibility Assessment

### ✅ Strengths
1. **Lockfile Present:** `uv.lock` with 6,377 lines, version-pinned
2. **Package Manager:** Modern `uv` tool (fast, reliable)
3. **Python Version Specified:** `>=3.9` in pyproject.toml
4. **Comprehensive Tests:** 5,340+ test functions across 276 files
5. **Policy Enforcement:** CI policy pack with critical path protection

### ⚠️ Gaps
1. **No CI Workflow Files:** No `.github/workflows/` directory found
   - Policy packs exist but unclear how/where they're enforced
   - No evidence of automated test runs on PRs

2. **Pytest Not in PATH:** May require `uv run pytest` or venv activation
   - Not a blocker, but adds friction

3. **Many Linter Rules Disabled:** Ruff ignores many rules for "legacy code"
   - May hide code quality issues

4. **No Documented Build Process:** No `Makefile` targets for standard builds
   - Wait, there IS a Makefile - need to check it

### 🔍 Further Investigation Needed
- Check if CI runs externally (GitHub Actions, GitLab CI, etc.)
- Verify test execution: `uv run pytest -m smoke` (smoke tests)
- Review Makefile for build automation
- Confirm reproducibility: same inputs → same outputs

## Commands for Verification

```bash
# Verify lockfile integrity
uv lock --check

# Run smoke tests (fast)
uv run pytest -m smoke -v

# Run full test suite (may be slow)
uv run pytest -v

# Check linter
uv run ruff check src/

# Verify build
uv build
```

## Related Findings
- FND-0004: CI workflow evidence gap (to be created)
