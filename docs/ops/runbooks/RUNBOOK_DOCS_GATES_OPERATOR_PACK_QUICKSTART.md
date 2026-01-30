# RUNBOOK — Docs Gates Operator Pack — Quick Start

**Status:** ACTIVE  
**Scope:** Docs / CI Gates / Operator Workflow  
**Risk:** LOW (docs-only gates, snapshot-based validation)  
**Last Updated:** 2026-01-13

## Purpose

This runbook provides a **single-page quick reference** for the Docs Gates Operator Pack, which includes three CI gates that enforce documentation quality and prevent common errors.

**Problem:** Operators need a fast, reliable way to validate docs changes locally before pushing to CI.

**Solution:** A single snapshot-based helper script that reproduces all 3 docs gates locally, with clear PASS/FAIL output and actionable next steps.

## What's Included

**3 CI Gates:**
1. **Docs Token Policy Gate** — Enforces encoding policy for illustrative paths in inline-code spans
2. **Docs Reference Targets Gate** — Validates that all referenced file paths actually exist
3. **Docs Diff Guard Policy Gate** — Ensures policy markers are present in required operator docs

**Operator Tools:**
- **Snapshot Helper Script:** `scripts&#47;ops&#47;pt_docs_gates_snapshot.sh` — One command to run all 3 gates
- **3 Detailed Runbooks:** Comprehensive triage guides for each gate (400+ lines each)

## Quick Start (60 Seconds)

### Step 1: Run Snapshot Helper (Changed Files)

```bash
# From repo root
./scripts/ops/pt_docs_gates_snapshot.sh --changed
```

**Expected Output:**
```
🔍 Gate 1/3: Docs Token Policy Gate
✅ Docs Token Policy Gate: PASS

🔍 Gate 2/3: Docs Reference Targets Gate
✅ Docs Reference Targets Gate: PASS

🔍 Gate 3/3: Docs Diff Guard Policy Gate
✅ Docs Diff Guard Policy Gate: PASS

🎉 All gates passed! Docs changes are merge-ready.
```

### Step 2: If Any Gate Fails

Follow the **"Next Actions"** printed in the output. Each gate provides:
- Specific failure details
- Actionable fix commands
- Link to detailed runbook

### Step 3: Re-run After Fixes

```bash
./scripts/ops/pt_docs_gates_snapshot.sh --changed
```

**Done!** If all gates pass, commit and push.

## Common Commands

### Quick Validation (PR Workflow)

```bash
# Default: check changed files only (fast, <10s)
./scripts/ops/pt_docs_gates_snapshot.sh --changed

# Against specific base branch
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/develop
```

### Full Repo Audit

```bash
# Scan entire repo (slow, ~30s)
./scripts/ops/pt_docs_gates_snapshot.sh --all
```

### Individual Gates (If Needed)

```bash
# Token Policy Gate only
python3 scripts/ops/validate_docs_token_policy.py --changed

# Reference Targets Gate only
bash scripts/ops/verify_docs_reference_targets.sh --changed

# Diff Guard Policy Gate only
python3 scripts/ci/check_docs_diff_guard_section.py
```

## Troubleshooting

### All 3 Gates: Common Issues

#### Issue: "Script hangs at prompt (> or dquote>)"

**Cause:** Shell continuation mode (unclosed quote or heredoc)

**Fix:**
```bash
# Press Ctrl-C to abort
# Check for unclosed quotes in script args
```

**Prevention:** Script includes pre-flight hint at startup.

#### Issue: "Permission denied"

**Cause:** Script not executable

**Fix:**
```bash
chmod +x scripts/ops/pt_docs_gates_snapshot.sh
```

#### Issue: "uv: command not found"

**Cause:** Missing `uv` dependency

**Fix:**
```bash
pip install uv
# Or see docs/ops/README.md for installation
```

### Gate 1: Docs Token Policy Gate

**Most Common Failure:** Illustrative path without encoding

**Symptom:**
```
Line 42: `scripts/example.py` (ILLUSTRATIVE) <!-- pt:ref-target-ignore -->
  → Illustrative path token must use encoding
```

**Quick Fix:**
```markdown
Replace: `scripts/example.py` <!-- pt:ref-target-ignore -->
With:    `scripts&#47;example.py`
```

**Detailed Guide:** [RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md)

### Gate 2: Docs Reference Targets Gate

**Most Common Failure:** File renamed/moved without updating docs

**Symptom:**
```
Missing targets: 1
  - docs/ops/GUIDE.md:42: scripts&#47;old_name.py
```

**Quick Fix:**
```bash
# Option A: Update docs to new path
sed -i 's|scripts&#47;old_name.py|scripts&#47;new_name.py|g' docs/ops/GUIDE.md

# Option B: Encode as illustrative (if intentional example)
# Change: `scripts/old_name.py` → `scripts&#47;old_name.py` <!-- pt:ref-target-ignore -->
```

**Detailed Guide:** [RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md)

### Gate 3: Docs Diff Guard Policy Gate

**Most Common Failure:** Policy marker missing in required docs

**Symptom:**
```
❌ Docs Diff Guard Policy: section marker missing in required docs.
   Missing in:
    - docs/ops/NEW_GUIDE.md
```

**Quick Fix:**
```bash
# Auto-insert marker
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/NEW_GUIDE.md

# Verify
python3 scripts/ci/check_docs_diff_guard_section.py
```

**Detailed Guide:** [RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md)

## Decision Tree: Which Command to Use?

```
Docs change scenario
         ↓
    PR workflow (daily use)?
    ├─ YES → ./scripts/ops/pt_docs_gates_snapshot.sh --changed
    │         (Fast: <10s, strict validation)
    │
    └─ NO → Post-refactor audit?
            ├─ YES → ./scripts/ops/pt_docs_gates_snapshot.sh --all
            │         (Slow: ~30s, respects ignore lists)
            │
            └─ NO → Single gate troubleshooting?
                    → Run individual gate command (see above)
```

## No-Watch Philosophy

**Important:** All commands in this pack are **snapshot-only**.

**What This Means:**
- ✅ Run once, get result, exit
- ✅ Clear PASS/FAIL output
- ✅ No background processes
- ✅ No polling or watching
- ✅ Safe for CI and local use

**Why:**
- Deterministic behavior
- No terminal hangs
- Easy to script and chain
- Cursor Agent-friendly

**If You Need Watch Mode:**
This is **not** supported by design. Use snapshot commands in a loop if needed:

```bash
# NOT RECOMMENDED (use with caution)
while true; do
  ./scripts/ops/pt_docs_gates_snapshot.sh --changed
  sleep 30
done
```

## Operator Workflow: Docs Change Checklist

**Before Committing:**
1. Run snapshot helper: `./scripts/ops/pt_docs_gates_snapshot.sh --changed`
2. If failures: Follow "Next Actions" in output
3. Re-run until all gates pass
4. Commit: `git add . && git commit`

**Before Pushing:**
1. Quick recheck: `./scripts/ops/pt_docs_gates_snapshot.sh --changed`
2. Push: `git push -u origin <branch>`

**After PR Created:**
- CI will run same gates automatically
- If CI fails but local passed: Fetch main and re-run against `origin&#47;main`

**If PR is BEHIND main:**
- Merge/rebase main into your branch
- Re-run snapshot helper to validate after merge

## Integration with CI

**Automatic CI Gates:**
All 3 gates run automatically on PRs that touch Markdown files.

**Workflow Files:**
- Token Policy: `.github&#47;workflows&#47;docs-token-policy-gate.yml`
- Reference Targets: `.github&#47;workflows&#47;docs-reference-targets-gate.yml`
- Diff Guard Policy: `.github&#47;workflows&#47;ci.yml` (inline check)

**Check Status:**
```bash
# View all PR checks
gh pr checks <PR_NUMBER>

# Filter docs gates
gh pr checks <PR_NUMBER> | grep -E "docs-token|docs-reference|Docs Diff"
```

**Matching Local and CI Behavior:**
```bash
# Match CI exactly (uses origin/main as base)
git fetch origin main
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

## References

### Detailed Runbooks (400+ lines each)

1. **[RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md)**
   - Token classification rules
   - Encoding policy details
   - Allowlist management
   - Comprehensive troubleshooting

2. **[RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md)**
   - File path validation rules
   - Relative vs absolute paths
   - Ignore list management
   - False positive triage

3. **[RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md)**
   - Policy marker format
   - Required docs list
   - Auto-insertion script usage
   - Trigger path rules

### Scripts & Tools

**Snapshot Helper:**
- `scripts&#47;ops&#47;pt_docs_gates_snapshot.sh` (332 lines, snapshot-only)

**Individual Gate Validators:**
- `scripts&#47;ops&#47;validate_docs_token_policy.py` (Token Policy)
- `scripts&#47;ops&#47;verify_docs_reference_targets.sh` (Reference Targets)
- `scripts&#47;ci&#47;check_docs_diff_guard_section.py` (Diff Guard Policy)

**Helper Tools:**
- `scripts&#47;ops&#47;insert_docs_diff_guard_section.py` (Policy marker insertion)
- `scripts&#47;ops&#47;docs_token_policy_allowlist.txt` (Token allowlist)
- `docs&#47;ops&#47;DOCS_REFERENCE_TARGETS_IGNORE.txt` (Reference targets ignore list)

### CI Workflows

- `.github&#47;workflows&#47;docs-token-policy-gate.yml`
- `.github&#47;workflows&#47;docs-reference-targets-gate.yml`
- `.github&#47;workflows&#47;ci.yml` (includes Diff Guard Policy check)

### Frontdoors

- **Ops README:** `docs&#47;ops&#47;README.md` (Section: "Docs Gates — Operator Pack")
- **Control Center:** `docs&#47;ops&#47;control_center&#47;AI_AUTONOMY_CONTROL_CENTER.md` (Quick Actions)

### Related PRs

- **PR #702:** Docs Gates Operator Pack v1.1 (this quickstart + optional CI signal)
- **PR #701:** Docs Gates Operator Pack v1.0 (3 runbooks + snapshot helper)
- **PR #700:** Docs Token Policy Gate Operator Runbook
- **PR #693:** Docs Token Policy Gate implementation + tests
- **PR #691:** Workflow notes integration + encoding policy formalization
- **PR #690:** Docs frontdoor + crosslink hardening

---

**Version:** 1.1  
**Owner:** ops  
**Maintainer:** Peak_Trade Operator Team
