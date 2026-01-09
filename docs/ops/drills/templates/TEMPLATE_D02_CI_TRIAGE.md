# D02 CI Triage — [DRILL_NAME]

**Date:** YYYY-MM-DD HH:MM  
**Operator:** [operator_id]  
**Drill ID:** [e.g., D03B, D04, etc.]  
**PR Number:** [e.g., #633] (if applicable)  
**Session ID:** [optional: unique session identifier]

---

## Purpose

Deterministic CI monitoring + failure drill-down. Uses **D03A method** (no `--watch` timeouts).

**Output:**
- CI status report
- Failure logs (if any)
- Fix applied (if needed)
- Verification (re-poll)

**Not for:**
- Pre-drill evidence (use TEMPLATE_D01_EVIDENCE_PACK.md)
- Post-drill closeout (use TEMPLATE_D03A_CLOSEOUT.md)

---

## D03A Method (3 Steps)

Canonical CI status check workflow:

### Step 1: Snapshot PR Checks (No Watch)

```bash
# Pre-Flight
cd /Users/frnkhrz/Peak_Trade || cd "$(git rev-parse --show-toplevel)"
pwd
git status -sb

# Get PR number (if on PR branch)
PR="$(gh pr view --json number -q .number 2>/dev/null || echo "<PR_NUMBER>")"

# Snapshot current check status (deterministic, no timeout risk)
gh pr checks ${PR}
```

**Output:**
```
[Paste terminal output here]
```

**Observation:**
- **PR Number:** [PR #]
- **Total Checks:** [count]
- **Passing:** [count]
- **Failing:** [count]
- **Pending:** [count]
- **Skipped:** [count]

**Status:** [ALL GREEN / FAILURES DETECTED / PENDING]

---

### Step 2: Identify Failing Checks + Details URL

**Only if failures detected in Step 1.**

```bash
# Extract only non-successful checks with details URLs
gh pr view ${PR} --json statusCheckRollup --jq '
  .statusCheckRollup[]
  | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED")
  | "\(.name): \(.status) / \(.conclusion)\n  URL: \(.detailsUrl // .targetUrl // "NO_URL")"
'
```

**Output:**
```
[Paste terminal output here]
```

**Failing Checks:**

| Check Name | Status | Conclusion | Details URL |
|------------|--------|------------|-------------|
| [Check 1] | [status] | [conclusion] | [URL] |
| [Check 2] | [status] | [conclusion] | [URL] |
| ... | ... | ... | ... |

---

### Step 3: Pull Failing Logs Deterministically

**Only if failures detected in Step 2.**

```bash
# Extract run ID from details URL or use gh run list
RUN_ID="<RUN_ID>"  # From Step 2 output

# Get failed logs only (deterministic, no streaming)
gh run view ${RUN_ID} --log-failed
```

**Output:**
```
[Paste terminal output here (first 50 lines)]
```

**Root Cause Analysis:**

| Check Name | Root Cause | Evidence |
|------------|------------|----------|
| [Check 1] | [e.g., "Missing target: docs/some-file.md"] | [line number in log output] |
| [Check 2] | [e.g., "Lint error: line 123"] | [line number in log output] |
| ... | ... | ... |

---

## Fix Applied (If Needed)

**Only if failures detected and fixable.**

### Problem Statement

[Describe the failure root cause from Step 3]

**Example:**
```
docs-reference-targets-gate failed: branch name "docs/drill-xyz"
interpreted as pseudo-path (false positive)
```

---

### Fix Strategy

[Describe how to fix the issue]

**Example:**
```
Add `<!-- pt:ref-target-ignore -->` after branch name mentions
in run log (3 instances at lines 10, 76, 391)
```

---

### Fix Commands

```bash
# Pre-Flight
cd /Users/frnkhrz/Peak_Trade || cd "$(git rev-parse --show-toplevel)"
pwd
git status -sb

# [Command 1: description]
[command]

# [Command 2: description]
[command]

# [Command 3: description]
[command]

# Verify fix locally
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

**Output:**
```
[Paste terminal output here]
```

**Observation:**
- **Fix applied:** [Y/N]
- **Local verification:** [PASS / FAIL]
- **Committed:** [Y/N]
- **Pushed:** [Y/N]

---

## Re-Poll (Verification)

**After fix pushed, wait 20-30s and re-poll.**

### Step 1 (Re-run): Snapshot PR Checks

```bash
# Wait for CI to trigger on new commit
sleep 30

# Re-poll
gh pr checks ${PR}
```

**Output:**
```
[Paste terminal output here]
```

**Observation:**
- **Total Checks:** [count]
- **Passing:** [count]
- **Failing:** [count]
- **Pending:** [count]

**Status:** [ALL GREEN / STILL FAILING / IMPROVED]

---

### Comparison (Before vs. After Fix)

| Metric | Before Fix | After Fix | Change |
|--------|------------|-----------|--------|
| **Passing** | [count] | [count] | [+/- count] |
| **Failing** | [count] | [count] | [+/- count] |
| **Pending** | [count] | [count] | [+/- count] |

**Assessment:** [FIX SUCCESSFUL / PARTIAL FIX / FIX FAILED]

---

## Polling Loop (Optional)

**If long-running checks (audit, Cursor Bugbot), use safe polling loop.**

```bash
# Safe polling loop (20s interval = rate-limit safe)
while true; do
  date
  gh pr checks ${PR} | head -25
  echo "----"
  sleep 20
done
# Press Ctrl-C when all checks GREEN
```

**Observation:**
- **Loop started:** [Y/N]
- **Total iterations:** [count]
- **Final status:** [ALL GREEN / STILL PENDING]
- **Stopped at:** [timestamp]

---

## CI Status Summary

### Final Check Status

| Status | Count | Check Names |
|--------|-------|-------------|
| ✅ **Passing** | [count] | [list or note "see output above"] |
| ❌ **Failing** | [count] | [list or note "see output above"] |
| ⏳ **Pending** | [count] | [list or note "see output above"] |
| ➖ **Skipped** | [count] | [list or note "see output above"] |

---

### Timeline (Triage → Fix → Verify)

| Event | Timestamp | Duration | Notes |
|-------|-----------|----------|-------|
| **Triage Start** | [HH:MM] | — | Step 1: Snapshot |
| **Failure Identified** | [HH:MM] | [+X min] | Step 2: Drill-down |
| **Root Cause Found** | [HH:MM] | [+X min] | Step 3: Logs |
| **Fix Applied** | [HH:MM] | [+X min] | Local verify + push |
| **Re-Poll** | [HH:MM] | [+X min] | Step 1 (re-run) |
| **All GREEN** | [HH:MM] | [Total: X min] | CI verified |

**Total Cycle Time:** [X minutes]

---

### Method Effectiveness

**D03A Method:**
- ✅ Deterministic (no timeout risk)
- ✅ Fast failure detection (<10s)
- ✅ Precise drill-down (exact error line)
- ✅ Reproducible (same output format)

**Comparison to `--watch`:**
- **Before (with --watch):** [estimated time, e.g., "10-15 min with timeout risk"]
- **After (D03A method):** [actual time, e.g., "5 min, no timeout"]
- **Improvement:** [percentage or time saved]

---

## Risk Assessment (CI)

**Risk Level:** [LOW / MED / HIGH]

**Rationale:**
- [Factor 1: e.g., "All required checks passing"]
- [Factor 2: e.g., "No flaky checks detected"]
- [Factor 3: e.g., "CI stable (no repeated failures)"]

**Concerns (if any):**
- [Concern 1: e.g., "Check X still pending after 10 min"]
- [Concern 2: e.g., "Check Y failed 2 times before passing (flaky?)"]

**Recommendation:** [PROCEED TO CLOSEOUT / DEFER / ESCALATE]

---

## Evidence Pointers

| ID | Type | Location | Note |
|----|------|----------|------|
| E01 | Terminal Output | Step 1 output | Initial PR status |
| E02 | CI Check URL | Step 2 output | Failing check details |
| E03 | Log Output | Step 3 output | Root cause line |
| E04 | Fix Verification | Local verify output | docs-reference-targets pass |
| E05 | Re-Poll Output | Step 1 (re-run) | All checks GREEN |

---

## References

**D03A Method:**
- [RUNBOOK_CI_STATUS_POLLING_HOWTO.md](../../runbooks/RUNBOOK_CI_STATUS_POLLING_HOWTO.md) — Canonical 3-step method

**Drill Pack:**
- [DRILL_PACK_M01_D03A_STANDARD.md](../DRILL_PACK_M01_D03A_STANDARD.md)

**Past Runs:**
- [DRILL_RUN_20260109_D03A_CI_POLLING.md](../runs/DRILL_RUN_20260109_D03A_CI_POLLING.md) — Example of complete triage cycle

**Operator Drill Pack:**
- [OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md](../OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md)

---

## Change Log

- **[Date]:** CI triage completed (operator: [name])
