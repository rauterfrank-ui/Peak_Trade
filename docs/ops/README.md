# Operations Guide

Quick reference for Peak_Trade operational tasks.

---

## Audit System

### Quick Commands

```bash
# Run full audit (local)
make audit

# Or directly
./scripts/run_audit.sh
```

**Exit Codes:**
- `0` - All critical checks passed (GREEN)
- `1` - Warnings/findings but no hard failures (YELLOW)
- `2` - Critical failure - failing tests or secrets detected (RED)

**Output Location:**
- Timestamped: `reports/audit/YYYY-MM-DD_HHMM/`
- Latest (symlink): `reports/audit/latest/`
- Machine-readable: `reports/audit/latest/summary.json`

### CI/CD Integration

**GitHub Actions:**
- Workflow: `.github/workflows/audit.yml`
- Schedule: Weekly (Mondays 06:00 UTC)
- Manual trigger: Actions → Audit → Run workflow
- Artifacts: Download from workflow run

**Accessing Artifacts:**
1. Go to `https://github.com/rauterfrank-ui/Peak_Trade/actions`
2. Click on latest "Audit" workflow run
3. Download `audit-artifacts.zip`
4. Extract and review `summary.md` and `summary.json`

### Audit Checks

The audit system runs:

1. **Repository Health**
   - Git status, commit history, branch info
   - Disk usage analysis
   - Git maintenance recommendations

2. **Security Scans**
   - Secrets detection (API keys, tokens, private keys)
   - Live trading gate verification (~340 safety gates)

3. **Code Quality** (optional tools)
   - `ruff` - Fast Python linter
   - `black` - Code formatting check
   - `mypy` - Type checking
   - `bandit` - Security issue detection
   - `pip-audit` - Dependency vulnerability scan

4. **Testing**
   - `pytest` - Full test suite
   - `todo-board-check` - TODO board validation

### Install Optional Tools

```bash
# Show install commands
make audit-tools

# Install all at once
pip install ruff black mypy pip-audit bandit
brew install ripgrep  # macOS only
```

### Interpreting Results

**Green (Exit 0):**
- All critical checks passed
- Safe to deploy/merge

**Yellow (Exit 1):**
- Warnings present (e.g., todo-board issues, high secrets hits)
- Review `summary.md` for details
- Not a blocker, but investigate

**Red (Exit 2):**
- Critical failure (tests failing)
- **DO NOT DEPLOY**
- Fix issues before proceeding

### Machine-Readable Output

```bash
# Parse latest audit with jq
cat reports/audit/latest/summary.json | jq '.status.audit_exit_code'

# Check pytest status
cat reports/audit/latest/summary.json | jq '.exit_codes.pytest'

# Get findings count
cat reports/audit/latest/summary.json | jq '.findings'
```

**JSON Schema (v1.1):**
```json
{
  "audit_version": "1.1",
  "timestamp": "YYYY-MM-DD_HHMM",
  "timestamp_iso": "ISO 8601 timestamp",
  "repo": {
    "branch": "branch-name",
    "commit_sha": "full-sha",
    "commit_short": "short-sha"
  },
  "tool_availability": { "tool": true|false },
  "exit_codes": {
    "pytest": "0|SKIPPED|exit_code",
    "todo_board": "0|SKIPPED|exit_code"
  },
  "findings": {
    "secrets_hits": 123,
    "live_gating_hits": 456
  },
  "status": {
    "overall": "GREEN|YELLOW|RED",
    "audit_exit_code": 0
  }
}
```

---

## CI Smoke Tests

### Quick Commands

```bash
# Run fast lane deterministic smoke tests (<3 min)
make ci-smoke
```

**Output Location:**
- Reports: `test_results/ci_smoke/`
- Files: `junit.xml`, `pytest.txt`, `env.txt`, JSON, MD

**Operator Guide:**
- Details: `docs/ops/ci_smoke_fastlane.md`

---

## Git Maintenance

```bash
# Pack git objects (safe)
make gc

# Preview ignored files to clean
git clean -ndX

# Remove ignored files (CAUTION: irreversible!)
git clean -fdX
```

---

## Related Documentation

- `scripts/run_audit.sh` - Audit script implementation
- `docs/ops/PYTHON_VERSION_PLAN.md` - Python upgrade roadmap
- `docs/ops/AUDIT_VALIDATION_NOTES.md` - Baseline validation findings
- `Makefile` - All available make targets

---

*Operations guide for Peak_Trade repository health and maintenance.*
