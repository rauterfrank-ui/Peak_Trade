# RUNBOOK — Docs Token Policy Gate — Operator Quick Reference

**Status:** ACTIVE  
**Scope:** Docs / CI Gates / Markdown Quality  
**Risk:** LOW (docs-only gate, non-blocking during 30-day burn-in)  
**Last Updated:** 2026-01-13

## Purpose

This runbook provides operator guidance for the **Docs Token Policy Gate**, which enforces an encoding policy for inline-code tokens in Markdown documentation to prevent false positives in the `docs-reference-targets-gate`.

**Problem:** Illustrative file paths (examples, placeholders) in inline-code spans trigger the reference-targets gate as "missing files."

**Solution:** Encode forward slashes in illustrative paths using HTML entity encoding, while exempting real repo paths, URLs, commands, and branch names.

## When to Run

**Automatic (CI):**
- Gate runs on all PRs touching Markdown files or the allowlist
- Workflow: `.github/workflows/docs-token-policy-gate.yml`
- Check status: `gh pr checks <PR_NUMBER> | grep "docs-token-policy-gate"`

**Manual (Local):**
- Before committing docs changes (recommended)
- When troubleshooting reference-targets-gate failures
- When updating the allowlist

## Quick Commands

### Local Validation (Changed Files)

```bash
# Default: check changed files only (fast, PR-mode)
python3 scripts/ops/validate_docs_token_policy.py --changed

# Check git-tracked docs only (docs/**/*.md)
python3 scripts/ops/validate_docs_token_policy.py --tracked-docs

# Full repo scan (slow, ~30s)
python3 scripts/ops/validate_docs_token_policy.py --all

# Generate JSON report
python3 scripts/ops/validate_docs_token_policy.py --changed --json report.json
```

### Exit Codes
- `0` = All checks passed (merge-ready)
- `1` = Violations found (see report for fixes)
- `2` = Error (invalid arguments, file not found)

## Common Failure Patterns

### Pattern 1: Illustrative Path Without Encoding

**Symptom:**
```
Line 42: `scripts/example.py` (ILLUSTRATIVE) <!-- pt:ref-target-ignore -->
  → Illustrative path token must use encoding
```

**Fix:**
Replace forward slash with HTML entity inside inline-code span:

```markdown
Before: `scripts/example.py`
After:  `scripts&#47;example.py`
```

**Rendering:** Both display identically (entity decoded to `/` in rendered view)

**Alternative (Perl one-liner for non-README files):** If the validator names a different file (e.g., `docs/ops/README.md`), apply common token fixes:

```bash
perl -0777 -i -pe 's/allowed=True\/False/allowed=True&#47;False/g; s/allowed=False\/True/allowed=False&#47;True/g; s/True\/False/True&#47;False/g; s/False\/True/False&#47;True/g' <path>
```

### Pattern 2: Real File Flagged as Illustrative

**Symptom:**
```
Line 15: `src/new_module.py` (ILLUSTRATIVE)
```

**Diagnostic:**
```bash
# Verify file exists
ls -la src/new_module.py

# If file exists but is new (not yet committed):
git add src/new_module.py
git commit -m "add new module"

# Re-run validator (should now classify as REAL_REPO_TARGET)
python3 scripts/ops/validate_docs_token_policy.py --changed
```

### Pattern 3: Branch Name False Positive

**Symptom:**
```
Line 23: `feature/my-branch` (BRANCH_NAME)
  → Illustrative path token must use encoding
```

**Fix:**
Branch names are **exempt** from encoding. If flagged, this is a classifier bug. Workaround:

```markdown
Option A: Add to allowlist (if used frequently)
Option B: Encode anyway (safe, but not required)
```

### Pattern 4: Generic Placeholder (Allowlist Candidate)

**Symptom:**
```
Multiple files reference `some/path` (used in 5+ docs)
```

**Fix:**
Add to allowlist with rationale:

```bash
# Edit allowlist
echo "# Generic placeholder for tutorial examples" >> scripts/ops/docs_token_policy_allowlist.txt
echo "some/path" >> scripts/ops/docs_token_policy_allowlist.txt

# Commit
git add scripts/ops/docs_token_policy_allowlist.txt
git commit -m "docs(ops): allowlist generic placeholder some/path"
```

**When to Allowlist:**
- Generic placeholders used in 3+ docs
- System paths (e.g., `/usr/local/bin`)
- Third-party paths (outside repo scope)

**When NOT to Allowlist:**
- Project-specific illustrative paths (encode instead)
- One-off examples in a single doc
- Real repo paths (auto-exempted)

### Pattern 5: Both Gates Fail (Token Policy + Reference Targets)

**Symptom:**
- Token Policy Gate: PASS
- Reference Targets Gate: FAIL (missing targets)

**Cause:**
Token Policy only checks **inline-code** spans (single backticks). Reference Targets checks **all** path-like patterns (links, plain text, etc.).

**Fix:**
See [RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md](RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md) for comprehensive triage.

## Token Classification Quick Reference

| Pattern | Example | Action | Reason |
|---------|---------|--------|--------|
| ILLUSTRATIVE | `scripts&#47;fake.py` | Encode (`&#47;`) | Doesn't exist in repo |
| REAL_REPO_TARGET | `src/core/config.py` | NO encoding | File exists |
| BRANCH_NAME | `feature/x`, `fix/y` | NO encoding | Branch pattern |
| URL | `https://example.com/path` | NO encoding | URL detected |
| COMMAND | `bash python3 scripts/ops/validate_docs_token_policy.py --help` | NO encoding | Command prefix |
| LOCAL_PATH | `/usr/local/bin`, `~/config` | NO encoding | Local prefix |
| ALLOWLISTED | `some/path` | NO encoding | In allowlist |

## Decision Tree: `--changed` vs `--all`

**Use `--changed` (default):**
- Daily PR workflow
- Fast (2-10 files, <5s)
- Recommended for local pre-commit checks

**Use `--all`:**
- Post-merge audit
- Gate logic changed (classifier updates)
- Allowlist cleanup
- Slow (~30s for entire repo)

## Interaction with Reference Targets Gate

**Relationship:**
- **Reference Targets Gate:** Verifies all inline-code tokens refer to real files (or are explicitly skipped)
- **Token Policy Gate (this):** Enforces encoding for illustrative paths so they DON'T trigger Reference Targets Gate

**Example:**
```markdown
❌ Before (triggers Reference Targets Gate):
`scripts/example.py` (gate thinks this is a missing file) <!-- pt:ref-target-ignore -->

✅ After (safe for both gates):
`scripts&#47;example.py` (gate ignores this as it's not a valid path)
```

## Troubleshooting

### Issue: "I encoded the path but it still fails"

**Cause:** Encoding applied in fenced code block instead of inline-code span.

**Fix:** Only encode inline-code (single backticks). Fenced blocks (triple backticks) are automatically ignored.

### Issue: "Copy/paste includes `&#47;` entity"

**Cause:** User copied from raw Markdown instead of rendered view.

**Fix:** Copy from **rendered view** (GitHub UI). Browsers decode entities automatically.

### Issue: "Gate is too strict"

**Cause:** Classification heuristics might be overly conservative.

**Fix:**
1. Check if token should be in different category (e.g., is it a command?)
2. Add to allowlist if it's a known exception
3. Open ticket to adjust classifier if systematic issue

## Fixing a failure (targeted)

If the validator reports a file other than `README.md`, apply the fix **only** to that file:

```bash
perl -0777 -i -pe 's/allowed=True\/False/allowed=True&#47;False/g; s/allowed=False\/True/allowed=False&#47;True/g; s/True\/False/True&#47;False/g; s/False\/True/False&#47;True/g' <path>
```

Example: `perl -0777 -i -pe '...' docs&#47;ops&#47;README.md`

## Maintenance

### Allowlist Hygiene

**File:** `scripts/ops/docs_token_policy_allowlist.txt`

**PR Requirements:**
- MUST include rationale (inline comment or block comment)
- MUST have clear commit message
- Reviewer MUST verify rationale is present

**Example:**
```text
# Generic placeholder for tutorial examples (used in 5+ docs)
some/path

# System path for macOS Homebrew installations
/usr/local/bin
```

**Quarterly Audit:**
- Remove stale entries
- Consolidate duplicates
- Verify rationale clarity

## References

**Full Documentation:**
- [RUNBOOK_DOCS_TOKEN_POLICY_GATE.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE.md) — Comprehensive guide (373 lines)
- [RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md](RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md) — Reference Targets triage

**Scripts & Tests:**
- Validator: `scripts/ops/validate_docs_token_policy.py`
- Tests: `tests/ops/test_validate_docs_token_policy.py` (26 unit tests)
- Allowlist: `scripts/ops/docs_token_policy_allowlist.txt`
- CI Workflow: `.github/workflows/docs-token-policy-gate.yml`

**Related PRs:**
- PR #693: Implementation + tests + runbook
- PR #691: Policy formalization
- PR #690: First application of encoding

---

**Version:** 1.0  
**Owner:** ops
