# Docs Reference Targets: Safe Markdown Guide

**Version:** 1.0.0  
**Date:** 2026-01-12  
**Status:** Active  
**Audience:** Operators writing docs/ops merge logs, runbooks, and PRs

---

## Purpose

The docs-reference-targets CI gate validates that all file paths referenced in Markdown docs actually exist in the repository. This prevents broken links and missing file references.

**However**, the gate can produce **false positives** when certain non-file identifiers (like branch names or commit SHAs) are formatted in ways that resemble file paths.

This guide documents the **2 failure patterns** from Phase 5E and provides **safe formatting practices** to avoid triggering the gate unnecessarily.

---

## The 2 Failure Patterns

### Pattern 1: Backticks Around Branch Names

**Problem:** Branch names in backticks are detected as potential file paths.

**Example (UNSAFE):**
```
Merged branch `docs/merge-log-650` into main.
Rebased from `feat/my-feature` onto main.
```

**Why It Fails:**
- The gate sees path-like tokens: segment docs, slash, segment merge-log-650
- Attempts to validate as a file path
- File does not exist → FAIL

**When It Happens:**
- After branch deletion (post-merge)
- Branch name contains slashes (common in feat/, docs/, fix/ patterns)

---

### Pattern 2: References to Not-Yet-Merged Files

**Problem:** Documenting planned or in-progress file paths that do not yet exist in main.

**Example (UNSAFE):**
```
Implementation will add:
- `src/execution/recon_engine.py` (reconciliation logic)
- `docs/ops/RECON_RUNBOOK.md` (operator guide)
```

**Why It Fails:**
- Gate runs against main branch
- Files are planned for this PR but not yet merged
- File does not exist in main → FAIL

**When It Happens:**
- Merge logs written before PR is merged
- Architecture docs describing future components
- PRs that reference files from other pending PRs

---

## Safe Patterns (DO)

### Branch Names

**Option A: Plain text without backticks**
```
Merged branch docs/merge-log-650 into main.
Created from feature branch feat/phase-5e-guide.
```

**Option B: Explicit prefix (no code span)**
```
Branch: docs/merge-log-650 (deleted post-merge)
Source branch: feat/phase-5e-guide
```

**Option C: Link format (if branch still exists)**
```
[docs/merge-log-650](https://github.com/owner/repo/tree/docs/merge-log-650) (deleted)
```

---

### Commit SHAs

**Plain text or explicit label:**
```
Commit SHA: a1b2c3d4
Merge commit: d8b9c176
```

**Avoid:**
```
`a1b2c3d4` ← May be detected as potential file reference
```

---

### Planned/Future Files

**Option A: Generic description**
```
Implementation adds reconciliation engine and operator runbook.
```

**Option B: Component-level reference (no paths)**
```
Deliverables:
- Reconciliation engine (execution layer)
- Operator runbook (ops docs)
```

**Option C: Explicit marker**
```
Planned files (not yet in main):
- Reconciliation engine: src/execution/recon_engine.py
- Operator runbook: docs/ops/RECON_RUNBOOK.md
```

**Note:** The explicit marker approach works IF you are writing the doc in the same PR that introduces those files. Otherwise, use Option A or B.

---

### Files in Same PR

**Safe IF files are added in the SAME PR:**
```
This PR introduces:
- src/execution/recon_engine.py (reconciliation logic)
- docs/ops/RECON_RUNBOOK.md (operator guide)

Both files are part of this PR and will exist after merge.
```

**Why Safe:** The gate runs on the PR branch (after your changes), so files exist at validation time.

---

## Unsafe Patterns (DON'T)

### ❌ Backticks on Branch Names with Slashes
```
Branch `docs/merge-log-650` was deleted.
Rebased from `feat/phase-5e` onto main.
```

**Impact:** Gate interprets as missing file docs/merge-log-650

---

### ❌ Code Spans on Path-Like Non-Files
```
Working on `WP5E_implementation_v2` directory.
Label `ops/execution-reviewed` applied.
```

**Impact:** Gate may attempt to validate as paths (especially if containing slashes or looking like directory names)

---

### ❌ References to Files Not in Main (cross-PR)
```
See implementation in `src/risk/component_var.py` (from PR #408).
```

**Impact:** If PR #408 is not yet merged, file does not exist in main → FAIL

**Fix:** Use generic description or wait until PR #408 merges

---

## Local Verification (Before Push)

**Quick check (changed files only, CI parity):**
```bash
scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

**Exit Codes:**
- 0 = PASS (or not applicable, no Markdown changes)
- 1 = FAIL (missing targets detected)

**Full-scan audit (optional, includes legacy content):**
```bash
scripts/ops/verify_docs_reference_targets.sh
```

**Note:** Full-scan respects ignore patterns and exits with code 1 even on "PASS-with-notes" (legacy content expected to have some broken refs).

---

## CI Triage Checklist

**If docs-reference-targets-gate fails on your PR:**

1. **Read the failure output** (GitHub Actions log shows missing targets)
2. **Identify the pattern:**
   - Branch name in backticks? → Remove backticks or use plain text
   - File from another PR? → Use generic description or wait for dependency PR
   - Typo in existing file path? → Fix typo
3. **Apply fix** (see Safe Patterns section)
4. **Re-run locally:**
   ```bash
   scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
   ```
5. **Push fix** → CI re-runs automatically

---

## Examples (Real Cases from Phase 5E)

### Case 1: PR #651 (Branch Name False Positive)

**Original (UNSAFE):**
```
Branch `docs/merge-log-650` deleted post-merge.
```

**Fixed (SAFE):**
```
Branch docs/merge-log-650 deleted post-merge.
```

**Lesson:** Remove backticks from branch names with slashes.

---

### Case 2: PR #650 (Planned Files)

**Original (UNSAFE):**
```
Will implement:
- `src/ai_autonomy/l4_critic_validator.py`
- `docs/ops/L4_CRITIC_RUNBOOK.md`
```

**Fixed (SAFE):**
```
Will implement:
- L4 Critic Validator (AI Autonomy layer)
- L4 Critic Runbook (ops docs)
```

**Lesson:** Use component-level descriptions for not-yet-merged files.

---

### Case 3: PR #649 (10 Planned Paths)

**Original (UNSAFE):**
```
Deliverables:
- `docs/ops/PHASE4D_CURSOR_TRIAGE_PROMPT_L1.md`
- `docs/ops/PHASE4D_CURSOR_TRIAGE_PROMPT_L2.md`
- ... (8 more)
```

**Fixed (SAFE):**
```
Deliverables:
- Phase 4D Cursor Triage Prompts (10 files, L1-L5 layers)
```

**Lesson:** Batch references to planned files as a single summary line.

---

## Related Documentation

- **Gate Workflow:** .github/workflows/docs_reference_targets_gate.yml
- **Validator Script:** scripts/ops/verify_docs_reference_targets.sh
- **Ignore Patterns:** docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt (legacy content)
- **Style Guide:** docs/ops/DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md
- **Phase 5E Evidence:** docs/ops/PR_651_MERGE_LOG.md (Pattern Recognition section)

---

**End of Guide**
