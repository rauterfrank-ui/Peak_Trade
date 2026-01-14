# Pre-PR Full Scan (CI-Parity Mode) — Operator Guide

**Purpose:** Ensure local scans match CI behavior before PR creation, avoiding surprise CI failures.

**Context:** During Phase 9C Wave 3, CI detected a token-policy violation (`reports&#47;` on Line 35 of PHASE_16L) that local `--changed` scans missed. This guide establishes "CI-Parity" scanning to catch such issues early.

---

## Quick Reference

### Pre-PR Checklist (CI-Parity Mode)

Run these commands **before** creating a PR:

```bash
# 1. Full Docs Reference Targets Scan (no --changed flag)
scripts&#47;ops&#47;verify_docs_reference_targets.sh

# 2. Full Token Policy Scan (--all flag)
uv run python scripts&#47;ops&#47;validate_docs_token_policy.py --all

# 3. Changed-files scan (against main, for comparison)
uv run python scripts&#47;ops&#47;validate_docs_token_policy.py --changed --base main

# 4. Full Gates Snapshot (optional, comprehensive)
scripts&#47;ops&#47;pt_docs_gates_snapshot.sh
```

**Rule:** If **any** of these fail, fix locally before pushing.

---

## Modes Comparison

| Mode | Flag | Files Scanned | Use Case |
|------|------|---------------|----------|
| **Full Scan** | `--all` or none | All Markdown files in repo | Pre-PR verification (CI-Parity) |
| **Changed Files** | `--changed --base main` | Only files changed vs. main | Quick iteration during development |
| **Specific Files** | (file paths as args) | Specified files only | Targeted fixes |

**CI Behavior:** CI typically runs in **Full Scan** mode or **Changed Files vs. origin&#47;main** mode.

**Risk:** `--changed` mode may miss violations in files not yet committed or in upstream changes.

---

## Detailed Commands

### 1. Docs Reference Targets Gate

**Purpose:** Verify all Markdown links resolve to existing files.

```bash
# Full Scan (CI-Parity)
scripts&#47;ops&#47;verify_docs_reference_targets.sh

# Expected output: "Missing targets: N" (where N is the current broken count)
# Goal: No increase in N from baseline
```

**Notes:**
- No `--full` flag needed (default mode is full scan)
- Script ignores 9 specified directories (e.g., `venv&#47;`, `.git&#47;`)
- Reports: Line number + missing target path

### 2. Token Policy Gate

**Purpose:** Verify inline-code tokens follow escape rules (`&#47;` for `/`).

```bash
# Full Scan (CI-Parity)
uv run python scripts&#47;ops&#47;validate_docs_token_policy.py --all

# Expected output: "✅ All checks passed!" or "❌ Found N violation(s) in M file(s)"
```

**Changed Files Scan (for comparison):**
```bash
# Against main
uv run python scripts&#47;ops&#47;validate_docs_token_policy.py --changed --base main

# Against custom base
uv run python scripts&#47;ops&#47;validate_docs_token_policy.py --changed --base origin&#47;feature-branch
```

**Notes:**
- `--all` scans **all** Markdown files (1177 files as of 2026-01-14)
- `--changed` scans only files modified vs. base branch
- CI uses `--changed --base origin&#47;main`

### 3. Full Gates Snapshot

**Purpose:** Run all docs gates in one command.

```bash
# Full snapshot (saves to docs&#47;ops&#47;graphs&#47;)
scripts&#47;ops&#47;pt_docs_gates_snapshot.sh

# Expected output:
# - Docs Token Policy Gate: PASS/FAIL
# - Docs Reference Targets Gate: PASS/FAIL
# - Docs Diff Guard Policy Gate: PASS/FAIL
```

**Notes:**
- Snapshot script runs both Token Policy + Reference Targets checks
- Saves results to timestamped JSON files
- Use for comprehensive pre-PR verification

---

## Best Practices

### When to Run Full Scans

1. **Before PR creation** (always)
2. **After batch remediation** (e.g., Wave 3, Wave 4)
3. **After upstream merge** (main → feature branch)
4. **When CI fails unexpectedly** (diagnose local vs. CI diff)

### When Changed-Files Scan is Sufficient

1. **During active development** (iterative fixes)
2. **For small, targeted changes** (1-2 files)
3. **When baseline is known clean** (no pre-existing violations)

### Avoiding "Surprise CI Failures"

**Problem:** Local `--changed` scan shows PASS, but CI fails with additional violations.

**Causes:**
1. **Upstream changes:** Main branch moved since your branch point
2. **Uncommitted files:** Local changes not yet committed
3. **Mode mismatch:** Local `--changed` vs. CI `--all` or CI `--changed --base origin&#47;main`

**Solution:**
- Always run **Full Scan** (`--all`) before PR creation
- After fixing, re-run **Changed Files Scan** to verify your fixes only
- Compare both outputs to ensure no regressions

---

## CI-Parity Workflow

### Recommended Pre-PR Flow

```bash
# Step 1: Ensure clean state
git status -sb
# Expected: "## your-branch...origin/main" (no uncommitted changes)

# Step 2: Full Scan (CI-Parity)
scripts&#47;ops&#47;verify_docs_reference_targets.sh | tee /tmp/pre_pr_targets.txt
uv run python scripts&#47;ops&#47;validate_docs_token_policy.py --all | tee /tmp/pre_pr_token_policy.txt

# Step 3: Review outputs
grep "Missing targets:" /tmp/pre_pr_targets.txt
grep "Found .* violation" /tmp/pre_pr_token_policy.txt

# Step 4: If violations found, fix locally
# (apply escapes, fix links, etc.)

# Step 5: Re-run changed-files scan to verify fixes
uv run python scripts&#47;ops&#47;validate_docs_token_policy.py --changed --base main

# Step 6: Commit + push
git add -A
git commit -m "docs: fix pre-PR violations"
git push

# Step 7: Create PR (CI should now pass)
gh pr create --base main --head your-branch --title "..." --body "..."
```

---

## Troubleshooting

### "CI fails but local scan passes"

**Diagnosis:**
1. Check CI logs for exact violation
2. Run local **Full Scan** (`--all`), not `--changed`
3. Compare CI base branch (`origin&#47;main`) vs. local base branch

**Fix:**
- Fetch latest main: `git fetch origin main`
- Rebase or merge: `git rebase origin&#47;main` or `git merge origin&#47;main`
- Re-run Full Scan

### "Full Scan reports thousands of violations"

**Context:** Wave 4 baseline showed **1860 violations in 469 files** (pre-existing, repo-wide).

**Strategy:**
1. **Focus on changed files first:** Use `--changed --base main`
2. **Document scope:** Note that full scan violations are out of scope for your PR
3. **Separate PRs:** Create follow-up PRs for repo-wide cleanup if needed

### "Script not found"

**Diagnosis:** Ensure you're in repo root:
```bash
pwd
# Expected: /Users/frnkhrz/Peak_Trade (or similar)

git rev-parse --show-toplevel
# Should match pwd
```

**Fix:** `cd` to repo root before running scripts.

---

## Examples

### Example 1: Wave 3 CI Surprise

**Scenario:** Wave 3 PR created after local `--changed` scan showed PASS. CI detected 1 violation in `PHASE_16L_DOCKER_OPS_RUNNER.md` Line 35: `reports/`.

**Root Cause:** File was modified in Wave 3, but the specific line (35) with `reports/` was not part of the initial changed hunks. CI's `--all` mode caught it.

**Prevention:** Run Full Scan before PR:
```bash
uv run python scripts&#47;ops&#47;validate_docs_token_policy.py --all
# Would have caught: Line 35: `reports/` (ILLUSTRATIVE)
```

**Lesson:** Always run Full Scan before PR creation, not just `--changed`.

### Example 2: Wave 4 Pre-PR Verification

**Scenario:** Wave 4 completed 22 target fixes. Before PR, operator runs Full Scan.

**Commands:**
```bash
# Full Reference Targets Scan
scripts&#47;ops&#47;verify_docs_reference_targets.sh
# Result: Missing targets: 65 (down from 87 ✅)

# Full Token Policy Scan
uv run python scripts&#47;ops&#47;validate_docs_token_policy.py --all
# Result: ✅ No new violations introduced (baseline: 1860 violations in 469 files, out of scope)

# Changed Files Scan (for comparison)
uv run python scripts&#47;ops&#47;validate_docs_token_policy.py --changed --base main
# Result: ✅ All checks passed! (8 files scanned)
```

**Outcome:** PR created with high confidence. CI passes without surprises.

---

## Related

- **Docs Token Policy Gate:** `.github&#47;workflows&#47;docs-token-policy-gate.yml`
- **Docs Reference Targets Gate:** `.github&#47;workflows&#47;docs-reference-targets-gate.yml`
- **Full Snapshot Script:** `scripts&#47;ops&#47;pt_docs_gates_snapshot.sh`
- **Validation Script:** `scripts&#47;ops&#47;validate_docs_token_policy.py`
- **Reference Targets Script:** `scripts&#47;ops&#47;verify_docs_reference_targets.sh`

---

**Version:** 1.0  
**Generated by:** Cursor Multi-Agent (Phase 9C Wave 4 Hardening)  
**Date:** 2026-01-14  
**Status:** ✅ Ready for Operator Use
