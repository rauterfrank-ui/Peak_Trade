# RUNBOOK — 3-Step CI Status Check (Deterministic Polling, No Watch)

**Status:** Operator-ready (v1.0)  
**Scope:** Docs-only operational guidance  
**Risk:** NONE (view-only operations, no code/config changes)  
**Owner:** Ops / AI Autonomy  
**Last updated:** 2026-01-09

---

## 0. Purpose & Guardrails

### Purpose

This runbook provides a standardized, **timeout-safe** method for monitoring PR CI status without using `--watch` flags.

**Problem Solved:**
- `gh pr checks --watch` frequently times out (>5 min)
- Non-deterministic results (hanging, inconsistent output)
- Blocks operator workflows during waits

**Solution:**
- Deterministic polling: `gh pr checks` without `--watch`
- Fast feedback: <10s per poll
- Rate-limit safe: ≤30s polling interval (2.4% of GitHub API limit)
- No timeout risk

### Guardrails (Non-negotiable)

- **Evidence-first:** Commands are deterministic and reproducible
- **No-live / Governance-locked:** View-only operations, no CI triggers
- **Rate-limit safe:** Follow 30s minimum polling interval

### Non-Goals

- Real-time streaming (use GitHub UI for that)
- Automated CI triggers or merges (operator monitors; automation is controlled via PR settings)
- Long-running background jobs (polls are manual or operator-controlled)

---

## 1. Quick Start (Copy-Paste)

### Single Poll (Instant Feedback)

```bash
# Get PR number automatically (if on PR branch)
PR="$(gh pr view --json number -q .number 2>/dev/null || echo "<PR_NUMBER>")"

# Snapshot current check status (no timeout risk)
gh pr checks ${PR}
```

**Expected Output:** Check list with name, status, elapsed time, URL (~10-20 checks, <10s response)

---

## 2. The "3-Step CI Status Check"

### Step 1: Snapshot PR Checks (No Watch)

**Command:**
```bash
PR="$(gh pr view --json number -q .number 2>/dev/null || echo "<PR_NUMBER>")"
gh pr checks ${PR}
```

**Output Example:**
```
NAME                         STATUS  ELAPSED  URL
docs-reference-targets-gate  pass    7s       https://github.com/...
lint-gate                    pass    5s       https://github.com/...
tests (3.10)                 pass    3s       https://github.com/...
Cursor Bugbot                pass    4m40s    https://cursor.com
```

**What It Shows:**
- ✅ Check name
- ✅ Status (pass / pending / fail / skipping)
- ✅ Elapsed time
- ✅ Direct URL to check details

**Why No `--watch`:**
- ❌ `--watch` risks >5 min timeout
- ❌ Non-deterministic (sometimes hangs, sometimes works)
- ✅ Without `--watch`: deterministic, instant (<10s), no timeout

---

### Step 2: Identify Failing Checks + Details URL

**Command:**
```bash
# Extract only non-successful checks with details URLs
gh pr view ${PR} --json statusCheckRollup --jq '
  .statusCheckRollup[]
  | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED")
  | "\(.name): \(.status) / \(.conclusion)\n  URL: \(.detailsUrl // .targetUrl // "NO_URL")"
'
```

**Output Example (if failures exist):**
```
docs-reference-targets-gate: COMPLETED / FAILURE
  URL: https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20864218710/job/59951198992
```

**Output (if all successful):**
```
(empty - no failures)
```

**Why This Command:**
- ✅ Filters noise (only shows PENDING, FAILURE, etc.)
- ✅ Provides direct link to failure logs
- ✅ Machine-parseable (JSON query)
- ✅ Copy-paste ready (output includes URLs)

---

### Step 3: Pull Failing Logs Deterministically

**Command:**
```bash
# Extract run ID from Step 2 URL or use gh run list
RUN_ID="20864218710"  # From Step 2 output

# Get failed logs only (no noise)
gh run view ${RUN_ID} --log-failed
```

**Alternative (if run ID not known):**
```bash
# Find latest run for current branch
gh run list --branch $(git branch --show-current) --limit 5

# Then use:
gh run view <RUN_ID> --log-failed
```

**Output:** Only failed job logs (no successful job noise)

**Why This Command:**
- ✅ Targets only failed jobs (efficient)
- ✅ Deterministic (repeatable)
- ✅ Offline-safe (can pipe to file: `gh run view <RUN_ID> --log-failed > failure.log`)

---

## 3. Safe Polling Loop (Optional)

**When to Use:** Monitoring PR during active CI run (waiting for checks to complete)

**Command:**
```bash
# Poll every 30s (rate-limit safe)
PR="$(gh pr view --json number -q .number 2>/dev/null || echo "<PR_NUMBER>")"

while true; do
  date '+%Y-%m-%dT%H:%M:%S%z'
  gh pr checks ${PR} | head -20  # Show top 20 checks
  echo "----"
  sleep 30
done
```

**How to Stop:** Press `Ctrl-C`

**Rationale:**
- ✅ 30s interval = 2 polls/min (well under GitHub rate limit: 5000 req/hour authenticated)
- ✅ Can be interrupted anytime
- ✅ No timeout risk (each poll is independent)
- ✅ Sustainable for hours if needed

**Rate-Limit Math:**
- 30s interval = 2 polls/min = 120 polls/hour
- GitHub API limit: 5000 req/hour (authenticated)
- Usage: 120/5000 = 2.4% of rate limit
- **Verdict:** SAFE for extended monitoring

---

## 4. Common Scenarios

### Scenario A: "Are my PR checks done?"

```bash
# Quick check (instant feedback)
gh pr checks <PR_NUMBER>

# Look for:
# - All "pass" → ready to merge
# - Any "pending" → still running
# - Any "fail" → needs attention
```

**Expected Time:** <10s

---

### Scenario B: "Which check failed?"

```bash
# Show only non-successful checks
gh pr view <PR_NUMBER> --json statusCheckRollup --jq '
  .statusCheckRollup[]
  | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED")
  | "\(.name): \(.conclusion)"
'
```

**Output Example:**
```
docs-reference-targets-gate: FAILURE
```

**Next Step:** Go to Step 3 (pull logs)

---

### Scenario C: "What's in the failure logs?"

```bash
# Get run ID from failure URL or:
gh run list --branch <BRANCH> --limit 5

# Pull failed logs
gh run view <RUN_ID> --log-failed
```

**Output:** Failure logs with line numbers and error messages

---

### Scenario D: "Monitor PR until all checks pass"

```bash
# Use polling loop (see Section 3)
# OR: Check every minute manually:
watch -n 60 'gh pr checks <PR_NUMBER> | head -20'
```

**Note:** `watch` command (Unix utility) is different from `gh pr checks --watch`. `watch -n 60` runs `gh pr checks` every 60s (safe).

---

## 5. Comparison: Watch vs. Polling

| Method | Timeout Risk | Determinism | Feedback Speed | Rate-Limit Safe | Operator Action |
|--------|--------------|-------------|----------------|-----------------|-----------------|
| `gh pr checks --watch` | ❌ HIGH (>5 min) | ❌ Non-deterministic | ⏳ Continuous | ❌ Risk (long connection) | Wait + hope |
| `gh pr checks` (no watch) | ✅ NONE | ✅ Deterministic | ✅ <10s | ✅ Yes | Instant result |
| Polling loop (30s) | ✅ NONE | ✅ Deterministic | ⏳ Every 30s | ✅ Yes (2.4% rate limit) | Ctrl-C to stop |

**Recommendation:** Always use `gh pr checks` without `--watch`. Use polling loop for active monitoring.

---

## 6. Troubleshooting

### Issue: "gh pr view: no pull requests found"

**Cause:** Not on a PR branch, or PR doesn't exist

**Fix:**
```bash
# Specify PR number explicitly
gh pr checks 632

# Or: Check current branch has a PR
gh pr view
```

---

### Issue: "gh run view: run not found"

**Cause:** Run ID is incorrect or run was deleted

**Fix:**
```bash
# List recent runs
gh run list --limit 10

# Find the run ID for your branch
gh run list --branch <BRANCH> --limit 5
```

---

### Issue: "Rate limit exceeded"

**Cause:** Too many API requests in short time (rare with 30s polling)

**Fix:**
```bash
# Check rate limit status
gh api rate_limit

# Wait for reset (shown in output)
# Or: Increase polling interval to 60s
```

---

## 7. Best Practices

### DO ✅

- ✅ Use `gh pr checks` without `--watch` for instant feedback
- ✅ Use 30s polling interval for active monitoring
- ✅ Stop polling loop when checks complete (Ctrl-C)
- ✅ Copy failure URLs from Step 2 for sharing with team
- ✅ Use `gh run view --log-failed` for efficient triage

### DON'T ❌

- ❌ Use `gh pr checks --watch` (timeout risk)
- ❌ Poll faster than 30s (unnecessary, rate-limit risk)
- ❌ Leave polling loop running indefinitely (wastes API calls)
- ❌ Use `gh run view --log` without `--failed` (too much noise)

---

## 8. Integration with Other Runbooks

### Control Center Operations

**Cross-Reference:** `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md`

**Section 8.2 "CI Watch timeouts / hängt":**
- **Old Method:** `gh pr checks --watch` (timeout-prone)
- **New Method:** Use this runbook's 3-Step CI Status Check (timeout-safe)

### Incident Triage

**Cross-Reference:** `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_INCIDENT_TRIAGE.md`

**Section 4 "Timeout-sichere Monitoring Methoden":**
- **Minimal-Polling via gh CLI:** Use Step 1 from this runbook
- **Evidence Capture:** Use Step 2 + Step 3 for failure triage

### Dashboard Operations

**Cross-Reference:** `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_DASHBOARD.md`

**Section 4 "PR/CI Monitoring":**
- **No-Watch Monitoring:** Use this runbook's polling methods

---

## 9. Examples (Real-World)

### Example 1: D02 PR #632 Failure Triage (2026-01-09)

**Context:** docs-reference-targets-gate failed during D02 drill

**Commands Used:**
```bash
# Step 1: Check status
gh pr checks 632
# → Identified 1 failing check

# Step 2: Get failure URL
gh pr view 632 --json statusCheckRollup --jq '...'
# → Got run ID: 20864218710

# Step 3: Pull logs
gh run view 20864218710 --log-failed
# → Found: 6 missing targets (forward refs + wrong path)
```

**Result:** Fixed in <30 min (triage → fix → verify → push)

**Reference:** `docs/ops/drills/D02_NEXT_DRILL_SELECTION_20260109.md`

---

### Example 2: D03A Polling Validation (2026-01-09)

**Context:** Validate 30s polling interval for D03A drill

**Commands Used:**
```bash
# Run 1 (T+0s)
gh pr checks 632

# Run 2 (T+30s)
sleep 30 && gh pr checks 632

# Run 3 (T+60s)
sleep 30 && gh pr checks 632
```

**Result:** All 3 runs successful, no timeouts, deterministic output

**Reference:** `docs/ops/drills/runs/DRILL_RUN_20260109_D03A_CI_POLLING.md`

---

## 10. Quick Reference Card (Copy-Paste)

```bash
# === 3-STEP CI STATUS CHECK ===

# STEP 1: Snapshot checks (instant feedback)
PR="$(gh pr view --json number -q .number 2>/dev/null || echo "<PR_NUMBER>")"
gh pr checks ${PR}

# STEP 2: Identify failures (if any)
gh pr view ${PR} --json statusCheckRollup --jq '
  .statusCheckRollup[]
  | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED")
  | "\(.name): \(.conclusion)\n  URL: \(.detailsUrl)"
'

# STEP 3: Pull failure logs
# (Use run ID from Step 2 URL)
gh run view <RUN_ID> --log-failed

# === OPTIONAL: POLLING LOOP (30s interval) ===
while true; do
  date && gh pr checks ${PR} | head -20 && echo "----" && sleep 30
done
# (Press Ctrl-C to stop)
```

---

## 11. References

**Drill Run:**
- `docs/ops/drills/runs/DRILL_RUN_20260109_D03A_CI_POLLING.md` — D03A execution log (validation evidence)

**Related Runbooks:**
- `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_DASHBOARD.md` — Control Center dashboard operations
- `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_INCIDENT_TRIAGE.md` — Incident triage (timeout workarounds)
- `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md` — Control Center operations (watch troubleshooting)

**D03A Charter:**
- `docs/ops/drills/D02_NEXT_DRILL_SELECTION_20260109.md` (lines 180-278) — D03A drill charter

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-09  
**Maintained By:** Peak_Trade Ops Team
