# PR — Docs Gates Operator Pack v1.1 (Quickstart + Optional BEHIND Signal)

## Summary

Adds a **single-entry Quickstart Runbook** and **optional informational CI workflow** to the Docs Gates Operator Pack (builds on PR #702). Reduces operator friction by consolidating all 3 docs gates into a 60-second workflow with clear troubleshooting guidance. Optional PR merge-state signal provides early BEHIND visibility without blocking.

## Why

**Problem:**
- Operators need fast, actionable guidance for docs gates (currently 3 separate 400+ line runbooks)
- No early visibility when PR branch is BEHIND main (discovered late via CI failures)
- Frontdoor navigation could be clearer (which runbook to start with?)

**Solution:**
- Single-page Quickstart Runbook (60-second workflow, common fixes, decision tree)
- Optional CI workflow shows BEHIND status in PR checks (informational-only, never blocks)
- Enhanced frontdoor with clear "START HERE" signposting

## Changes

### New Files (2)

**1. Quickstart Runbook** (`docs&#47;ops&#47;runbooks&#47;RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md`, 485 lines)
- Quick Start (60 seconds): 3-step workflow (run → fix → re-run)
- Common Commands: PR workflow, full audit, individual gates
- Troubleshooting: Most common failures for each gate with quick fixes
- Decision Tree: --changed vs --all
- No-Watch Philosophy: Explicit snapshot-only guidance
- Operator Workflow Checklist: Before commit, before push, after PR
- Integration with CI: Match local and CI behavior
- References: Links to 3 detailed runbooks, scripts, CI workflows

**2. Optional CI Workflow** (`.github&#47;workflows&#47;ci-pr-merge-state-signal.yml`, 102 lines)
- Trigger: pull_request (opened, synchronize, reopened)
- Job: "PR Merge State Signal"
- Output: Job Summary with merge state (behind/ahead) + sync instructions
- Exit: ALWAYS 0 (success, non-blocking)
- Concurrency: One run per PR (cancel-in-progress)
- Features: Conditional warning (only if BEHIND), copy-paste sync commands, link to Quickstart

### Modified Files (1)

**3. Frontdoor Integration** (`docs&#47;ops&#47;README.md`, +12 lines)
- Added prominent Quickstart link (⭐ START HERE)
- Reorganized runbook links (Quickstart → Detailed guides)
- Added "Optional CI Signal" section with purpose and status
- Enhanced "When PR is BEHIND main" workflow guidance

**Total:** 3 files changed, +599 lines

## Verification

### Local Validation ✅

**Snapshot Helper (all gates):**
```bash
./scripts/ops/pt_docs_gates_snapshot.sh --changed
```
**Result:** ✅ All 3 gates passed (exit 0)

**Docs Reference Targets (runbooks):**
```bash
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs/ops/runbooks
```
**Result:** ✅ 33 md files, 215 references, all exist

**YAML Syntax:**
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci-pr-merge-state-signal.yml'))"
```
**Result:** ✅ Valid

**Linter:**
```bash
ruff check docs/ops/
```
**Result:** ✅ No errors

### Expected CI Behavior

**New Workflow:**
- Name: "PR Merge State Signal (Informational)"
- Trigger: All PRs (opened, synchronize, reopened)
- Status: ALWAYS SUCCESS (green check) ✅
- Output: Job Summary with BEHIND status + sync instructions
- Required: NO (not in `config&#47;ci&#47;required_status_checks.json`)

**Existing Gates (unchanged):**
- Docs Token Policy Gate
- Docs Reference Targets Gate
- Docs Diff Guard Policy Gate

## Risk

**Risk Level:** 🟢 LOW

**Why Low Risk:**
1. **Docs-only changes** (no production code)
2. **Additive** (no existing content removed)
3. **Optional CI workflow** (never required, always success)
4. **Snapshot-only** (no watch loops, no background processes)
5. **Gate-validated** (all links checked, YAML valid)

**Failure Modes:**
| Failure Mode | Likelihood | Impact | Mitigation |
|--------------|------------|--------|------------|
| Quickstart outdated | LOW | LOW | Cross-links to authoritative scripts |
| CI wrong status | LOW | NONE | Informational-only, never blocks |
| Links break | LOW | LOW | Docs-Reference-Targets-Gate validates |
| Operator confusion | LOW | LOW | Clear "START HERE" signposting |

**Rollback:** Simple revert (<5 minutes)

## Operator How-To

### 60-Second Quick Start

**Step 1: Run Snapshot Helper**
```bash
# From repo root
./scripts/ops/pt_docs_gates_snapshot.sh --changed
```

**Step 2: If Any Gate Fails**

**Token Policy Gate:**
```markdown
Replace: `scripts/example.py`
With:    `scripts&#47;example.py`
```

**Reference Targets Gate:**
```bash
sed -i 's|old_path|new_path|g' docs/file.md
```

**Diff Guard Policy Gate:**
```bash
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/file.md
```

**Step 3: Re-run**
```bash
./scripts/ops/pt_docs_gates_snapshot.sh --changed
```

**Expected:**
```
✅ Docs Token Policy Gate
✅ Docs Reference Targets Gate
✅ Docs Diff Guard Policy Gate
🎉 All gates passed! Docs changes are merge-ready.
```

**Step 4: Check PR Status (Optional)**

After PR created: Check "PR Merge State Signal" job summary
- **If BEHIND:** Follow sync instructions in job summary
- **If UP TO DATE:** No action needed

### Documentation

**Quick Reference (START HERE):**
- `docs&#47;ops&#47;runbooks&#47;RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md` ⭐

**Detailed Runbooks (400+ lines each):**
1. `docs&#47;ops&#47;runbooks&#47;RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md`
2. `docs&#47;ops&#47;runbooks&#47;RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md`
3. `docs&#47;ops&#47;runbooks&#47;RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md`

**Frontdoor:**
- `docs&#47;ops&#47;README.md` (Section: "Docs Gates — Operator Pack")

## What's New in v1.1

**v1.0 (PR #702, merged 2026-01-13):**
- 3 Operator Runbooks (Token Policy, Reference Targets, Diff Guard)
- Snapshot Helper Script (`pt_docs_gates_snapshot.sh`)
- Frontdoor integration (docs/ops/README.md)

**v1.1 (this PR):**
- ✨ **Quickstart Runbook** (single-page quick reference for all 3 gates)
- ✨ **PR Merge State Signal** (optional CI workflow for early BEHIND visibility)
- ✨ **Enhanced Frontdoor** (clear navigation with "START HERE" signposting)

## References

**Related PRs:**
- PR #702: Docs Gates Operator Pack v1.0 (baseline)
- PR #701: 3 runbooks + snapshot helper
- PR #700: Token Policy Gate Operator Runbook
- PR #693: Token Policy Gate implementation + tests
- PR #691: Encoding policy formalization
- PR #690: Docs frontdoor + crosslink hardening

**Scripts & Tools:**
- `scripts&#47;ops&#47;pt_docs_gates_snapshot.sh` (snapshot helper)
- `scripts&#47;ops&#47;validate_docs_token_policy.py` (Token Policy)
- `scripts&#47;ops&#47;verify_docs_reference_targets.sh` (Reference Targets)
- `scripts&#47;ci&#47;check_docs_diff_guard_section.py` (Diff Guard Policy)

**CI Workflows:**
- `.github&#47;workflows&#47;ci-pr-merge-state-signal.yml` (NEW, informational)
- `.github&#47;workflows&#47;docs-token-policy-gate.yml`
- `.github&#47;workflows&#47;docs-reference-targets-gate.yml`
- `.github&#47;workflows&#47;ci.yml` (includes Diff Guard check)

---

## Acceptance Criteria

- ✅ Ein klarer Single Entry Point: Quickstart + Script vorhanden
- ✅ Frontdoor/Control-Center verlinkt den Pack sichtbar
- ✅ Keine existierenden Inhalte entfernt
- ✅ Optionaler CI Workflow zeigt BEHIND früh, blockiert aber nie

---

**Version:** 1.1  
**Owner:** ops  
**Maintainer:** Peak_Trade Operator Team  
**Status:** READY TO MERGE
