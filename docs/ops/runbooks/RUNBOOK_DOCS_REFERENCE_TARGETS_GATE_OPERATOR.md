# RUNBOOK — Docs Reference Targets Gate — Operator Quick Reference

**Status:** ACTIVE  
**Scope:** Docs / CI Gates / Markdown Quality  
**Risk:** LOW (docs-only gate, blocks merge if missing targets found)  
**Last Updated:** 2026-01-13

## Purpose

This runbook provides operator guidance for the **Docs Reference Targets Gate**, which verifies that all file paths referenced in Markdown documentation actually exist in the repository.

**Problem:** Broken references after file renames, moves, or deletions cause dead links and maintenance debt.

**Solution:** Gate scans changed Markdown files, extracts path-like tokens, and validates existence. Operators fix by updating paths, encoding illustrative examples, or adding to ignore list.

## When to Run

**Automatic (CI):**
- Gate runs on all PRs touching Markdown files
- Workflow: `.github&#47;workflows&#47;docs-reference-targets-gate.yml`
- Check status: `gh pr checks <PR_NUMBER> | grep "docs-reference-targets"`

**Manual (Local):**
- Before committing docs changes (recommended)
- After file renames or moves
- When refactoring docs structure

## Quick Commands

### Local Validation (Changed Files)

```bash
# Default: check changed files only (fast, PR-mode)
bash scripts/ops/verify_docs_reference_targets.sh --changed

# Check against specific base branch
bash scripts/ops/verify_docs_reference_targets.sh --changed --base origin/develop

# Full repo scan (slow, ~30s)
bash scripts/ops/verify_docs_reference_targets.sh

# Warn-only mode (for ops doctor, exit 2 instead of 1)
bash scripts/ops/verify_docs_reference_targets.sh --warn-only
```

### Exit Codes
- `0` = All checks passed or not applicable (merge-ready)
- `1` = Missing targets found (blocks merge)
- `2` = Missing targets in warn-only mode (informational)

## Common Failure Patterns

### Pattern 1: File Renamed/Moved Without Updating Docs

**Symptom:**
```
Missing targets: 1
  - docs/ops/GUIDE.md:42: scripts/old_name.py
```

**Diagnostic:**
```bash
# Check if file exists with different name
find scripts -name "*old_name*" -o -name "*new_name*"

# Check git history for renames
git log --follow --all -- scripts/old_name.py
```

**Fix:**
```bash
# Update docs to reference new path
sed -i 's|scripts&#47;old_name.py|scripts&#47;new_name.py|g' docs/ops/GUIDE.md

# Verify fix
bash scripts/ops/verify_docs_reference_targets.sh --changed
```

### Pattern 2: Illustrative Example Path (False Positive)

**Symptom:**
```
Missing targets: 1
  - docs/tutorial.md:15: config&#47;my_example.toml
```

**Diagnostic:**
```bash
# Verify this is an example, not a real file
ls -la config/my_example.toml
# Output: No such file or directory → It's illustrative
```

**Fix Option A: Encode with HTML entity (recommended)**
```bash
# Replace forward slash with HTML entity in inline-code span
# Before: `config/my_example.toml`
# After:  `config&#47;my_example.toml`
```

**Fix Option B: Add to ignore list (for frequent placeholders)**
```bash
# Add to ignore file
echo "config/my_example.toml" >> docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt

# Commit
git add docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt
git commit -m "docs(ops): exempt illustrative path from reference targets gate"
```

**Note:** Option A is preferred for one-off examples. Option B for generic placeholders used across multiple docs.

### Pattern 3: Planned File (Not Yet Created)

**Symptom:**
```
Missing targets: 1
  - docs/roadmap.md:23: src&#47;new_feature.py
```

**Fix Option A: Create the file first**
```bash
# Create placeholder file
touch src/new_feature.py

# Commit
git add src/new_feature.py
git commit -m "feat: add new_feature.py placeholder"

# Verify gate passes
bash scripts/ops/verify_docs_reference_targets.sh --changed
```

**Fix Option B: Encode as illustrative (if file is hypothetical)**
```bash
# Use HTML entity encoding
# Change: `src/new_feature.py` → `src&#47;new_feature.py`
```

**Fix Option C: Use inline ignore marker**
```markdown
This feature will be implemented in `src/new_feature.py`. <!-- pt:ref-target-ignore -->
```

### Pattern 4: Multiple Files Reference Same Missing Target

**Symptom:**
```
Missing targets: 5
  - docs/ops/GUIDE1.md:42: scripts&#47;helper.py
  - docs/ops/GUIDE2.md:15: scripts&#47;helper.py
  - docs/ops/GUIDE3.md:88: scripts&#47;helper.py
  - docs/tutorial.md:12: scripts&#47;helper.py
  - docs/FAQ.md:55: scripts&#47;helper.py
```

**Diagnostic:**
```bash
# Check if file was deleted
git log --all --full-history -- scripts/helper.py

# Find all references
grep -r "scripts/helper.py" docs/
```

**Fix Option A: Restore file (if deleted by mistake)**
```bash
# Find last commit where file existed
git log --all --full-history -- scripts/helper.py

# Restore from specific commit
git checkout <commit_sha> -- scripts/helper.py
```

**Fix Option B: Update all references to new location**
```bash
# Find and replace across all docs
find docs -name "*.md" -type f -exec sed -i 's|scripts&#47;helper\.py|scripts&#47;utils&#47;helper.py|g' {} +

# Verify fix
bash scripts/ops/verify_docs_reference_targets.sh --changed
```

**Fix Option C: Add to ignore list (if intentionally removed)**
```bash
echo "scripts/helper.py" >> docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt
```

### Pattern 5: Relative Path Resolution Issue

**Symptom:**
```
Missing targets: 1
  - docs/ops/subdir/GUIDE.md:42: ../../../config/settings.toml
```

**Diagnostic:**
```bash
# Verify relative path resolution
cd docs/ops/subdir
ls -la ../../../config/settings.toml

# If file exists, check absolute path
realpath ../../../config/settings.toml
```

**Fix:**
```bash
# Option A: Use repo-relative path instead
# Change: `../../../config/settings.toml` → `config&#47;settings.toml`

# Option B: Fix relative path if incorrect
# Correct: `../../config/settings.toml` (if file is at repo root)
```

## Decision Tree: Illustrative vs Real Targets

```
Found missing target in docs
         ↓
    Does file exist?
    ├─ YES → Likely path resolution issue
    │         → Check relative vs absolute
    │         → Verify file is committed
    │
    └─ NO → Is this intentional?
            ├─ YES (illustrative example)
            │       → Encode with &#47; (preferred)
            │       → OR add to ignore list (generic placeholders)
            │
            └─ NO (should exist)
                    ├─ File renamed/moved?
                    │   → Update docs to new path
                    │
                    ├─ File deleted?
                    │   → Update docs or restore file
                    │
                    └─ Planned file?
                        → Create placeholder OR encode as illustrative
```

## Token Classification Quick Reference

| Pattern Type | Example | Gate Behavior | Action |
|--------------|---------|---------------|--------|
| Real repo file | `src&#47;core&#47;config.py` | Validates existence | Keep as-is |
| Illustrative path | `config&#47;example.toml` | Flags as missing | Encode with `&#47;` |
| Relative path | `.&#47;local&#47;file.md` | Resolves relative to doc | Keep as-is |
| URL | `https:&#47;&#47;github.com&#47;...` | Ignored | Keep as-is |
| Markdown link | `[text](target.md)` | Validates target | Update if broken |
| Inline code | `` `path&#47;to&#47;file` `` | Validates if path-like | Encode if illustrative |
| Fenced code block | ` ```path/to/file``` ` | Ignored | Keep as-is |

## Decision Tree: `--changed` vs Full Scan

**Use `--changed` (default):**
- Daily PR workflow
- Fast (2-10 files, <5s)
- Recommended for local pre-commit checks
- Strict: NO ignore patterns applied

**Use full scan (no `--changed`):**
- Post-refactor audit (file renames, moves)
- Periodic maintenance (quarterly cleanup)
- Ignore list cleanup
- Respects `DOCS_REFERENCE_TARGETS_IGNORE.txt`
- Slower (~30s for entire repo)

## Interaction with Token Policy Gate

**Relationship:**
- **Reference Targets Gate (this):** Validates ALL path-like tokens (links, inline-code, bare paths)
- **Token Policy Gate:** Enforces encoding ONLY for inline-code spans

**Example:**
```markdown
❌ Triggers Reference Targets Gate:
`scripts/example.py` (missing file in all detection modes)

✅ Safe for both gates:
`scripts&#47;example.py` (encoded, not detected as path)
```

**When both gates fail:**
1. Check Token Policy Gate first (faster, more specific)
2. Fix encoding violations
3. Re-run Reference Targets Gate
4. If still failing, follow Pattern 2 (Illustrative Example) above

## Troubleshooting

### Issue: "Gate passes locally but fails in CI"

**Cause:** CI uses `--changed` mode with merge-base; local might use different base.

**Fix:**
```bash
# Match CI behavior exactly
git fetch origin main
bash scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

### Issue: "Real file flagged as missing"

**Cause:** File exists but isn't committed yet, or in ignored directory.

**Fix:**
```bash
# Verify file is tracked
git ls-files src/my_file.py

# If not tracked, stage it
git add src/my_file.py

# Re-run gate
bash scripts/ops/verify_docs_reference_targets.sh --changed
```

### Issue: "Ignore list not working"

**Cause:** `--changed` mode does NOT respect ignore list (strict validation).

**Fix:**
```bash
# Option A: Encode illustrative paths instead of ignoring
# Option B: Run full scan to test ignore list
bash scripts/ops/verify_docs_reference_targets.sh  # no --changed
```

### Issue: "Too many false positives"

**Cause:** Docs contain many illustrative examples or planned features.

**Fix:**
```bash
# Audit and batch-fix illustrative paths
grep -r '`[^`]*/' docs/ | grep -v '&#47;' > /tmp/candidates.txt

# Review candidates, encode illustrative ones
# Use auto-fixer if available, or manual find/replace
```

## Maintenance

### Ignore List Hygiene

**File:** `docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt`

**When to add entries:**
- Generic placeholders used in tutorials (e.g., `some&#47;path`)
- External examples outside repo scope
- System paths (e.g., `&#47;usr&#47;local&#47;bin`)
- Planned features documented before implementation

**When NOT to add entries:**
- Real repo files (should exist)
- Typos (fix docs instead)
- One-off illustrative examples (encode with `&#47;` instead)

**Format:**
```text
# Generic tutorial placeholder
some/path

# Planned feature (Phase 5)
src/planned_module.py

# External dependency path
/usr/local/bin/custom_tool
```

**Quarterly Audit:**
```bash
# Review ignore list for stale entries
cat docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt

# Check if ignored paths now exist
while read -r path; do
  [[ "$path" =~ ^# ]] && continue
  [[ -f "$path" ]] && echo "EXISTS: $path (remove from ignore list?)"
done < docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt
```

### Post-Refactor Validation

After major docs restructuring:
```bash
# Full scan to catch all broken references
bash scripts/ops/verify_docs_reference_targets.sh

# Review and fix all violations
# Update ignore list if needed

# Re-scan to verify
bash scripts/ops/verify_docs_reference_targets.sh
```

## References

**Full Documentation:**
- [RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md](RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md) — Comprehensive false positive triage guide
- [Docs Reference Targets Safe Markdown Guide](../guides/DOCS_REFERENCE_TARGETS_SAFE_MARKDOWN.md) — Operator guide for avoiding false positives

**Scripts & Tests:**
- Validator: `scripts&#47;ops&#47;verify_docs_reference_targets.sh`
- Trend Tracker: `scripts&#47;ops&#47;verify_docs_reference_targets_trend.sh`
- Ignore List: `docs&#47;ops&#47;DOCS_REFERENCE_TARGETS_IGNORE.txt`
- CI Workflow: `.github&#47;workflows&#47;docs-reference-targets-gate.yml`

**Related Gates:**
- [Docs Token Policy Gate](RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md) — Encoding policy for inline-code tokens
- [Docs Diff Guard Policy Gate](RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md) — Policy section marker enforcement

**Related PRs:**
- PR #690: Docs frontdoor + crosslink hardening (first large-scale application)
- PR #693: Docs Token Policy Gate implementation

---

**Version:** 1.0  
**Owner:** ops
