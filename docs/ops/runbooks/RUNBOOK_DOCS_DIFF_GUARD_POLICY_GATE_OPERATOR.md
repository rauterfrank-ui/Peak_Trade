# RUNBOOK — Docs Diff Guard Policy Gate — Operator Quick Reference

**Status:** ACTIVE  
**Scope:** Docs / CI Gates / Policy Enforcement  
**Risk:** LOW (docs-only gate, blocks merge if policy marker missing)  
**Last Updated:** 2026-01-13

## Purpose

This runbook provides operator guidance for the **Docs Diff Guard Policy Gate**, which enforces the presence of a standardized policy marker section in key ops documentation files.

**Problem:** Policy documentation can be accidentally removed or forgotten during refactors, leading to incomplete operator guidance.

**Solution:** Gate checks that required docs contain the marker `"Docs Diff Guard (auto beim Merge)"` when relevant files change. Operators fix by inserting the policy section.

## When to Run

**Automatic (CI):**
- Gate runs when PRs touch specific trigger paths:
  - `docs/ops/` (any file)
  - `scripts/ops/review_and_merge_pr.sh`
  - `scripts/ops/docs_diff_guard.sh`
- Workflow: `.github/workflows/ci.yml` (inline policy check)
- Check status: `gh pr checks <PR_NUMBER> | grep "Docs Diff Guard"`

**Manual (Local):**
- Before committing changes to `docs/ops/` files
- When updating PR management documentation
- During quarterly docs audits

## Quick Commands

### Local Validation

```bash
# Run policy check (matches CI behavior)
python3 scripts/ci/check_docs_diff_guard_section.py

# Auto-insert marker in specific files
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/README.md

# Insert in multiple files (comma-separated)
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/PR_MANAGEMENT_TOOLKIT.md,docs/ops/PR_MANAGEMENT_QUICKSTART.md
```

### Exit Codes
- `0` = Policy marker present or not applicable (merge-ready)
- `1` = Policy marker missing in required docs (blocks merge)

## Common Failure Patterns

### Pattern 1: New Ops Doc Without Policy Marker

**Symptom:**
```
❌ Docs Diff Guard Policy: section marker missing in required docs.
   Marker: Docs Diff Guard (auto beim Merge)
   Missing in:
    - docs/ops/NEW_GUIDE.md
```

**Diagnostic:**
```bash
# Check if file is tracked
git ls-files docs/ops/NEW_GUIDE.md

# Verify marker is actually missing
grep -n "Docs Diff Guard" docs/ops/NEW_GUIDE.md
```

**Fix:**
```bash
# Auto-insert policy section
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/NEW_GUIDE.md

# Verify insertion
grep -A5 "Docs Diff Guard" docs/ops/NEW_GUIDE.md

# Commit
git add docs/ops/NEW_GUIDE.md
git commit --amend --no-edit

# Verify gate passes
python3 scripts/ci/check_docs_diff_guard_section.py
```

### Pattern 2: Marker Removed During Refactor

**Symptom:**
```
❌ Docs Diff Guard Policy: section marker missing in required docs.
   Missing in:
    - docs/ops/PR_MANAGEMENT_TOOLKIT.md
```

**Diagnostic:**
```bash
# Check git diff to see if marker was removed
git diff origin/main docs/ops/PR_MANAGEMENT_TOOLKIT.md | grep -C3 "Docs Diff Guard"

# Check history
git log -p --all -S "Docs Diff Guard" -- docs/ops/PR_MANAGEMENT_TOOLKIT.md
```

**Fix:**
```bash
# Re-insert policy section
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/PR_MANAGEMENT_TOOLKIT.md

# Review diff to ensure no content was lost
git diff docs/ops/PR_MANAGEMENT_TOOLKIT.md

# Commit
git add docs/ops/PR_MANAGEMENT_TOOLKIT.md
git commit -m "docs(ops): restore diff guard policy marker"
```

### Pattern 3: Marker Present But Malformed

**Symptom:**
```
❌ Docs Diff Guard Policy: section marker missing in required docs.
```

**Diagnostic:**
```bash
# Check for similar text (typo, spacing)
grep -i "diff guard" docs/ops/GUIDE.md
grep -i "docs.*guard" docs/ops/GUIDE.md

# Expected exact match:
grep "Docs Diff Guard (auto beim Merge)" docs/ops/GUIDE.md
```

**Fix:**
```bash
# Option A: Manual fix (if marker is close)
# Edit file and correct marker text to exact string:
#   "Docs Diff Guard (auto beim Merge)"

# Option B: Re-insert with script (replaces existing section)
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/GUIDE.md
```

### Pattern 4: Multiple Files Missing Marker

**Symptom:**
```
❌ Docs Diff Guard Policy: section marker missing in required docs.
   Missing in:
    - docs/ops/PR_MANAGEMENT_TOOLKIT.md
    - docs/ops/PR_MANAGEMENT_QUICKSTART.md
    - docs/ops/README.md
```

**Fix:**
```bash
# Batch insert with comma-separated list
python3 scripts/ops/insert_docs_diff_guard_section.py \
  --files docs/ops/PR_MANAGEMENT_TOOLKIT.md,docs/ops/PR_MANAGEMENT_QUICKSTART.md,docs/ops/README.md

# Verify all markers present
for f in docs/ops/PR_MANAGEMENT_TOOLKIT.md docs/ops/PR_MANAGEMENT_QUICKSTART.md docs/ops/README.md; do
  echo "Checking $f"
  grep -q "Docs Diff Guard (auto beim Merge)" "$f" && echo "  ✅ OK" || echo "  ❌ MISSING"
done

# Commit
git add docs/ops/PR_MANAGEMENT_TOOLKIT.md docs/ops/PR_MANAGEMENT_QUICKSTART.md docs/ops/README.md
git commit -m "docs(ops): add diff guard policy markers"
```

### Pattern 5: Gate Fails But Marker Is Present

**Symptom:**
```
❌ Docs Diff Guard Policy: section marker missing in required docs.
   Missing in:
    - docs/ops/README.md
```

**Diagnostic:**
```bash
# Verify marker is present
grep -n "Docs Diff Guard (auto beim Merge)" docs/ops/README.md

# Check for invisible characters (copy/paste artifacts)
hexdump -C docs/ops/README.md | grep -A2 -B2 "Diff Guard"

# Verify exact string match
python3 -c "
text = open('docs/ops/README.md').read()
marker = 'Docs Diff Guard (auto beim Merge)'
print(f'Marker present: {marker in text}')
print(f'Occurrences: {text.count(marker)}')
"
```

**Fix:**
```bash
# Re-insert with script (idempotent, safe)
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/README.md

# Verify fix
python3 scripts/ci/check_docs_diff_guard_section.py
```

## Decision Tree: When Policy Marker Is Required

```
Changed files in PR
         ↓
    Touches trigger paths?
    ├─ YES (docs/ops/, review_and_merge_pr.sh, docs_diff_guard.sh)
    │         ↓
    │   Check required docs:
    │   - PR_MANAGEMENT_TOOLKIT.md
    │   - PR_MANAGEMENT_QUICKSTART.md
    │   - README.md
    │         ↓
    │   All have marker?
    │   ├─ YES → ✅ Gate passes
    │   └─ NO  → ❌ Gate fails (insert marker)
    │
    └─ NO (other paths only)
            ↓
        ✅ Gate skipped (not applicable)
```

## Policy Marker Content

**Exact String Required:**
```
Docs Diff Guard (auto beim Merge)
```

**Typical Section Format:**
The insertion script adds a complete policy section. Example:

```markdown
## Docs Diff Guard (auto beim Merge)

**Policy:** This section ensures that docs changes are reviewed with governance context.

**Operator Checklist:**
- [ ] Docs changes align with current governance posture
- [ ] No execution-critical paths altered without evidence
- [ ] Cross-links updated if files renamed/moved

**Auto-Enforcement:** CI gate validates marker presence in key ops docs.
```

**Note:** The script inserts this automatically. Manual insertion must match the exact marker string.

## Minimal-Invasive Fix Strategy

**Principle:** Add marker without altering existing content.

**Step 1:** Always use auto-insertion script
```bash
python3 scripts/ops/insert_docs_diff_guard_section.py --files <path>
```

**Step 2:** Review diff before committing
```bash
git diff <path>
```

**Step 3:** If script altered existing content unintentionally:
```bash
# Revert and inspect
git checkout <path>

# Check current structure
head -50 <path>

# Manual insertion at appropriate section (usually near end, before references)
# Add exact marker: "Docs Diff Guard (auto beim Merge)"
```

**Step 4:** Verify minimal change
```bash
# Should show only addition of policy section
git diff --stat <path>
```

## Troubleshooting

### Issue: "Script fails with encoding error"

**Cause:** Non-UTF-8 characters in docs file.

**Fix:**
```bash
# Check file encoding
file -I docs/ops/GUIDE.md

# Convert to UTF-8 if needed
iconv -f ISO-8859-1 -t UTF-8 docs/ops/GUIDE.md -o docs/ops/GUIDE.md.utf8
mv docs/ops/GUIDE.md.utf8 docs/ops/GUIDE.md

# Re-run insertion
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/GUIDE.md
```

### Issue: "Insertion script adds marker in wrong place"

**Cause:** Script heuristics fail on unusual doc structure.

**Fix:**
```bash
# Revert auto-insertion
git checkout docs/ops/GUIDE.md

# Manual insertion:
# 1. Open file in editor
# 2. Add section near end (before References/Appendix)
# 3. Include exact marker string:
#    "Docs Diff Guard (auto beim Merge)"

# Verify
grep "Docs Diff Guard (auto beim Merge)" docs/ops/GUIDE.md
```

### Issue: "Gate passes locally but fails in CI"

**Cause:** CI might use different merge-base or file list.

**Fix:**
```bash
# Match CI behavior exactly
git fetch origin main
git diff --name-only origin/main...HEAD | grep -E "docs/ops/|review_and_merge_pr.sh|docs_diff_guard.sh"

# Run checker with same context
python3 scripts/ci/check_docs_diff_guard_section.py
```

### Issue: "Don't want marker in this specific doc"

**Cause:** File is in `docs/ops/` but not truly operator-critical.

**Fix:**
```bash
# Option A: Move file out of docs/ops/ (if appropriate)
git mv docs/ops/GUIDE.md docs/guides/GUIDE.md

# Option B: Request exemption via PR comment (rare, requires approval)
# Document rationale in PR body

# Option C: Add marker anyway (safest, no special handling needed)
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/GUIDE.md
```

## Maintenance

### Quarterly Audit

**Goal:** Ensure all `docs/ops/` files have policy marker where appropriate.

```bash
# List all docs/ops markdown files
find docs/ops -name "*.md" -type f | sort

# Check which have marker
for f in $(find docs/ops -name "*.md" -type f); do
  if grep -q "Docs Diff Guard (auto beim Merge)" "$f"; then
    echo "✅ $f"
  else
    echo "❌ $f (missing marker)"
  fi
done

# Decide which missing files need marker
# (Not all files require it; focus on operator/PR management docs)

# Batch-add to files that need it
python3 scripts/ops/insert_docs_diff_guard_section.py --files <comma-separated-list>
```

### Post-Refactor Validation

After major `docs/ops/` restructuring:
```bash
# Run policy check
python3 scripts/ci/check_docs_diff_guard_section.py

# If failures, batch-fix
python3 scripts/ops/insert_docs_diff_guard_section.py --files <files>

# Commit as separate docs policy hygiene PR
git add docs/ops/
git commit -m "docs(ops): restore diff guard policy markers post-refactor"
```

## References

**Scripts:**
- Policy Checker: `scripts/ci/check_docs_diff_guard_section.py`
- Marker Insertion: `scripts/ops/insert_docs_diff_guard_section.py`
- CI Workflow: `.github/workflows/ci.yml` (inline check)

**Required Docs (as of 2026-01-13):**
- `docs/ops/PR_MANAGEMENT_TOOLKIT.md`
- `docs/ops/PR_MANAGEMENT_QUICKSTART.md`
- `docs/ops/README.md`

**Trigger Paths:**
- `docs/ops/` (any file)
- `scripts/ops/review_and_merge_pr.sh`
- `scripts/ops/docs_diff_guard.sh`

**Related Gates:**
- [Docs Token Policy Gate](RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md) — Encoding policy for inline-code tokens
- [Docs Reference Targets Gate](RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md) — Path existence validation

**Policy Background:**
- See `docs/ops/README.md` section "Docs Diff Guard Policy" for rationale
- See `docs/ops/PR_MANAGEMENT_TOOLKIT.md` for merge workflow context

---

**Version:** 1.0  
**Owner:** ops
