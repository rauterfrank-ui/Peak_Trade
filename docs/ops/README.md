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

## CI Fast Lane

- **Pull Requests (Fast Lane):** nur **Python 3.11** (schnelles Feedback, typ. ~3–4 min)
- **main (Full Matrix):** **Python 3.9 / 3.10 / 3.11** (vollständige Kompatibilitätsprüfung nach Merge)
- **Manuell & geplant:** Full Matrix via `workflow_dispatch` und `schedule`
- **Hardening:**
  - `fail-fast: false` (Matrix läuft vollständig durch, auch bei Fehlern)
  - `concurrency` mit `cancel-in-progress` (alte Runs werden abgebrochen)
  - **Timeouts:** `tests=20min`, `strategy-smoke=10min`

**Siehe auch:** `docs/ops/PR_45_FINAL_REPORT.md` (Audit/Verification Log zu PR #45)

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

## Audit Logs (Ops)
Konvention:
- Dateien: `docs/ops/PR_<NN>_FINAL_REPORT.md` (Verification Log pro PR)
- Regel: Wenn ein Ops-PR einen auditierbaren Verification Log erzeugt, hier verlinken.
- **Automation Runbook**: [PR_REPORT_AUTOMATION_RUNBOOK.md](PR_REPORT_AUTOMATION_RUNBOOK.md) – Generate, validate, and CI guard PR reports

- PR #45 – CI Fast Lane Verification Log: `docs/ops/PR_45_FINAL_REPORT.md`
- PR #51 – Live Session Evaluation CLI: `docs/ops/PR_51_FINAL_REPORT.md`
- PR #53 – Final Closeout Report: `docs/ops/PR_53_FINAL_REPORT.md`
- PR #59 – Final Report: `docs/ops/PR_59_FINAL_REPORT.md`
- PR #61 – Final Report: `docs/ops/PR_61_FINAL_REPORT.md`
- PR #62 – Final Report: `docs/ops/PR_62_FINAL_REPORT.md`
- PR #63 – Final Report: `docs/ops/PR_63_FINAL_REPORT.md`
- PR #66 – Final Report: `docs/ops/PR_66_FINAL_REPORT.md`
- PR #70 – Final Report: `docs/ops/PR_70_FINAL_REPORT.md`
- PR #73 – Final Report: `docs/ops/PR_73_FINAL_REPORT.md`
- PR #74 – Final Report: `docs/ops/PR_74_FINAL_REPORT.md`

---

## Merge Logs (Ops)
Post-merge documentation logs for operational PRs.

- PR #76 – Merge Log: `docs/ops/PR_76_MERGE_LOG.md`
- PR #85 – Merge Log: `docs/ops/PR_85_MERGE_LOG.md`
- PR #87 – Merge Log: `docs/ops/PR_87_MERGE_LOG.md`
- PR #90 – chore(ops): add git state + post-merge verification scripts – `docs/ops/PR_90_MERGE_LOG.md`
- PR #92 – Merge Log: `docs/ops/PR_92_MERGE_LOG.md`
- PR #93 – Merge Log: `docs/ops/PR_93_MERGE_LOG.md`
- PR #110 – feat(reporting): Quarto smoke report – `docs/ops/PR_110_MERGE_LOG.md`
- PR #112 – fix(reporting): make Quarto smoke report no-exec – `docs/ops/PR_112_MERGE_LOG.md`
- PR #114 – fix(reporting): make Quarto smoke report truly no-exec – `docs/ops/PR_114_MERGE_LOG.md`
- PR #116 – Merge Log: `docs/ops/PR_116_MERGE_LOG.md`
- PR #121 – chore(ops): default expected head in post-merge verify – `docs/ops/PR_121_MERGE_LOG.md`
- PR #136 – feat(stability): wave A contracts, cache integrity, errors, reproducibility – `docs/ops/PR_136_MERGE_LOG.md`
- PR #144 – docs(reporting): clean up doc paths, avoid tracking in ignored dirs – `docs/ops/PR_144_MERGE_LOG.md`

---
- PR #80 – Merge Log: `docs/ops/PR_80_MERGE_LOG.md`
## Live Session Evaluation

Offline tool for analyzing live trading sessions from `fills.csv`.

```bash
# Evaluate session
python scripts/evaluate_live_session.py --session-dir /path/to/session

# Generate JSON report
python scripts/evaluate_live_session.py \
  --session-dir /path/to/session \
  --write-report
```

**Key Features:**
- FIFO PnL calculation per symbol
- VWAP (overall + per symbol)
- Side breakdown (buy/sell stats)
- Offline only (no exchange/API calls)

**See:** `docs/ops/LIVE_SESSION_EVALUATION.md` for detailed runbook

---

## Related Documentation

- `scripts/run_audit.sh` - Audit script implementation
- `docs/ops/PYTHON_VERSION_PLAN.md` - Python upgrade roadmap
- `docs/ops/AUDIT_VALIDATION_NOTES.md` - Baseline validation findings
- `GIT_STATE_VALIDATION.md` – Git state validation utilities and usage
- `docs/ops/LIVE_SESSION_EVALUATION.md` - Live session evaluation runbook
- `docs/ops/WORKTREE_POLICY.md` - Git worktree management policy
- `Makefile` - All available make targets

---

*Operations guide for Peak_Trade repository health and maintenance.*