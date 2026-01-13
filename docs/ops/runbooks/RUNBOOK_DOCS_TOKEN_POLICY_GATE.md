---
title: Runbook – Docs Token Policy Gate
date: 2026-01-13
audience: devs, docs-authors, ci-maintainers
scope: CI gates, documentation quality
status: active
---

# Runbook: Docs Token Policy Gate

## Overview

The **Docs Token Policy Gate** enforces an encoding policy for inline-code tokens in Markdown documentation to prevent `docs-reference-targets-gate` false positives.

**Problem:** When illustrative (non-existent) file paths like:

```text
scripts/example.py
```

appear in inline-code spans, the `docs-reference-targets-gate` interprets them as missing files and fails CI.

**Solution:** Encode the forward slash (``&#47;``) as `&#47;` in illustrative paths, while leaving real repo targets, URLs, commands, and branch names unchanged.

---

## When This Gate Triggers

The gate scans changed Markdown files (`.md`) for inline-code tokens (single backticks: `` `token` ``) containing ``&#47;`` and enforces:

1. **ILLUSTRATIVE** paths (e.g., `scripts&#47;fake.py`, `config&#47;example.toml`) → **MUST** use `&#47;` encoding
2. **REAL_REPO_TARGET** (existing files) → **NO** encoding required
3. **BRANCH_NAME** patterns (e.g., ``feature&#47;my-feature``, `docs&#47;update`) → **NO** encoding required
4. **URL** (http/https) → **NO** encoding required
5. **COMMAND** (prefixed with `python `, `git `, etc.) → **NO** encoding required
6. **LOCAL_PATH** (starts with ``.&#47;``, ``..&#47;``, ``~&#47;``, or ``&#47;``) → **NO** encoding required
7. **ALLOWLISTED** tokens → **NO** encoding required

---

## Classification Examples

| Token | Classification | Encoding Required? | Reason |
|-------|----------------|-------------------|--------|
| `scripts&#47;example.py` | ENCODED | ✅ Already compliant | Forward slash already encoded |
| (See fenced block below) | ILLUSTRATIVE | ❌ **VIOLATION** | Looks like path but doesn't exist |
| `scripts&#47;real_script.py` | REAL_REPO_TARGET (if exists) | ✅ Compliant | File exists in repo |
| ``feature&#47;my-feature`` | BRANCH_NAME | ✅ Compliant | Branch name pattern (known prefix) |
| `docs&#47;update` | BRANCH_NAME | ✅ Compliant | Branch name pattern (known prefix) |
| `python scripts&#47;run.py` | COMMAND | ✅ Compliant | Command prefix detected |
| ``https:&#47;&#47;example.com&#47;path`` | URL | ✅ Compliant | URL detected |
| `.&#47;scripts&#47;local.py` | LOCAL_PATH | ✅ Compliant | Local path prefix |
| ``some&#47;path`` | ILLUSTRATIVE (if allowlisted) | ✅ Compliant | In allowlist |

**Example of ILLUSTRATIVE violation (shown in fenced block to avoid triggering gate):**

```text
scripts/example.py
config/example.toml
```

---

## How to Fix Violations

### Step 1: Identify Violations

When the gate fails, you'll see output like:

```
❌ Found 2 violation(s) in 1 file(s):

📄 docs/GUIDE.md
  Line 15: ``scripts&#47;example.py`` (ILLUSTRATIVE)
    → Illustrative path token must use &#47; encoding
    💡 Replace ``scripts&#47;example.py`` with `scripts&#47;example.py`

  Line 23: ``feature&#47;my-branch`` (BRANCH_NAME)
    → Illustrative path token must use &#47; encoding
    💡 Replace ``feature&#47;my-branch`` with `feature&#47;my-branch`
```

### Step 2: Apply the Fix

**Option A: Manual Fix**

Replace the forward slash with `&#47;` inside the inline-code span:

```diff
- Here's an example: ``scripts&#47;example.py``.
+ Here's an example: `scripts&#47;example.py`.

- Checkout branch: ``feature&#47;my-branch``.
+ Checkout branch: `feature&#47;my-branch`.
```

**Option B: Automated Fix (Python Script)**

## Auto-Fix Scripts

This gate is intentionally strict. If it fails due to inline-code tokens that look like paths/commands/endpoints, use the auto-fixer to apply a conservative, targeted escape.

### Recommended (v2, conservative)
Use v2 first. It is selective and avoids rewriting URLs and fenced code blocks. Re-running is safe (idempotent).

```bash
# Preview changes (dry-run)
python3 scripts/ops/autofix_docs_token_policy_inline_code_v2.py --dry-run <file1.md> <file2.md>

# Apply fixes
python3 scripts/ops/autofix_docs_token_policy_inline_code_v2.py --write <file1.md> <file2.md>

# Verify gates pass
uv run python scripts/ops/validate_docs_token_policy.py --changed
bash scripts/ops/verify_docs_reference_targets.sh --changed
```

**Option C: Add to Allowlist (If Appropriate)**

If a token is a generic placeholder (e.g., ``some&#47;path``) used across many docs:

1. Add it to ``scripts&#47;ops&#47;docs_token_policy_allowlist.txt``:

```txt
# Generic placeholders
some/path
path/to/file
```

2. Commit the allowlist update with your changes.

---

## What NOT to Encode

**Do NOT encode these:**

1. **Real repo file paths** that exist:
   ```markdown
   ✅ ``scripts&#47;run_backtest.py`` (if file exists)
   ```

2. **URLs**:
   ```markdown
   ✅ ``https:&#47;&#47;github.com&#47;user&#47;repo&#47;blob&#47;main&#47;file.py``
   ```

3. **Commands** with path arguments:
   ```markdown
   ✅ ``python scripts&#47;run.py``
   ✅ ``git diff origin&#47;main``
   ```

4. **Local path patterns**:
   ```markdown
   ✅ ``.&#47;scripts&#47;local.py``
   ✅ ``..&#47;config&#47;file.toml``
   ✅ ``~&#47;Documents&#47;file.txt``
   ```

5. **Fenced code blocks** (triple backticks):
   ````markdown
   ```bash
   # This is ignored by the gate
   cd scripts/example/
   python fake.py
   ```
   ````

---

## Verification Commands

### Local Testing (Before Push)

```bash
# Test changed files (default mode)
python scripts/ops/validate_docs_token_policy.py

# Test all Markdown files
python scripts/ops/validate_docs_token_policy.py --all

# Test with custom base ref
python scripts/ops/validate_docs_token_policy.py --base origin/develop

# Generate JSON report
python scripts/ops/validate_docs_token_policy.py --json report.json
```

### CI Verification

The gate runs automatically on all PRs. Check the workflow:

```bash
gh pr checks <PR_NUMBER> | grep "Docs Token Policy Gate"
```

---

## Interaction with docs-reference-targets-gate

**Relationship:**

- **docs-reference-targets-gate**: Verifies that all inline-code tokens in docs refer to real files in the repo (or are explicitly skipped).
- **docs-token-policy-gate** (this gate): Enforces that illustrative paths use `&#47;` encoding so they DON'T trigger `docs-reference-targets-gate`.

**Example:**

```markdown
❌ Before (triggers docs-reference-targets-gate):
``scripts&#47;example.py`` (gate thinks this is a missing file)

✅ After (safe for both gates):
`scripts&#47;example.py` (gate ignores this as it's not a valid path)
```

---

## Troubleshooting

### Issue: "I encoded the path but it still fails"

**Cause:** You might have encoded it in a fenced code block instead of an inline-code span.

**Fix:** Only encode inline-code (single backticks). Fenced code blocks (triple backticks) are automatically ignored.

### Issue: "My real file path is flagged as ILLUSTRATIVE"

**Cause:** The file might not exist in your branch yet, or the script can't find it.

**Fix:**
1. Verify the file exists: `ls -la <path>`
2. If it's a new file, commit it first, then run the validator.
3. If it's intentionally illustrative, encode it.

### Issue: "I want to use a generic placeholder across many docs"

**Cause:** Encoding every instance is tedious.

**Fix:** Add the token to the allowlist:
```bash
echo "my/generic/placeholder" >> scripts/ops/docs_token_policy_allowlist.txt
```

### Issue: "The gate is too strict"

**Cause:** The classification heuristics might be overly conservative.

**Fix:**
1. Check if your token should be in a different category (e.g., is it a command?).
2. Add it to the allowlist if it's a known exception.
3. If it's a systematic issue, open a ticket to adjust the classifier.

---

## Maintenance

### Allowlist Maintenance

The allowlist is at ``scripts&#47;ops&#47;docs_token_policy_allowlist.txt``.

**Decision Rules: When to Allowlist vs. Fix Docs Tokenization**

| Scenario | Action | Rationale |
|----------|--------|-----------|
| Generic placeholder used in 3+ docs | **Allowlist** | Avoids repetitive encoding across many files |
| System path (e.g., ``&#47;usr&#47;local&#47;bin``) | **Allowlist** | Not a repo path, semantically correct |
| Third-party path (e.g., external lib) | **Allowlist** | Outside repo scope |
| Illustrative path in 1-2 docs | **Encode** (`&#47;`) | Keeps allowlist focused, explicit per-doc |
| Typo or mistake | **Fix docs** | Correct the error, don't hide it |
| Real repo path | **No action** | Validator auto-exempts (REAL_REPO_TARGET) |

**PR Hygiene: Rationale Requirements**

When adding entries to the allowlist, **MUST** include rationale:

**Option 1: Inline comment (preferred)**
```text
# Generic placeholder for tutorial examples (used in 5+ docs)
some/path

# System path for macOS Homebrew installations
/usr/local/bin
```

**Option 2: Block comment for related entries**
```text
# --- Tutorial Placeholders ---
# Used across docs/tutorials/ for generic examples
some/path
your/config.toml
example/strategy.py
```

**Enforcement:**
- **PR Review:** Reviewer MUST verify rationale is present
- **Quarterly Audit:** Remove stale entries, consolidate duplicates, verify rationale clarity

**When to add entries:**
- Generic placeholders used in tutorials (e.g., ``some&#47;path``)
- Common system paths (e.g., ``&#47;usr&#47;local&#47;bin``)
- Third-party paths (e.g., ``&#47;var&#47;log``)
- Patterns used in 3+ docs

**When NOT to add entries:**
- Project-specific illustrative paths (use `&#47;` encoding instead)
- One-off examples in a single doc
- Typos or mistakes (fix the docs)
- Real repo paths (auto-exempted by validator)

**Verification: How to Run Validator**

**Local (before commit):**
```bash
# Check changed files only (fast, PR-mode)
uv run python scripts/ops/validate_docs_token_policy.py --changed

# Check specific directory
uv run python scripts/ops/validate_docs_token_policy.py docs/ops/

# Full scan (slow, ~30s for entire repo)
uv run python scripts/ops/validate_docs_token_policy.py --all
```

**CI (automatic):**
- Runs on every PR touching ``docs&#47;**&#47;*.md`` or ``scripts&#47;ops&#47;docs_token_policy_allowlist.txt``
- Workflow: ``.github&#47;workflows&#47;docs-token-policy-gate.yml``
- Check status: `gh pr checks <PR_NUMBER> | grep "docs-token-policy-gate"`

**Exit Codes:**
- `0` = All checks passed
- `1` = Violations found (see report)
- `2` = Error (e.g., invalid arguments, file not found)

### Updating Classification Logic

If you need to adjust how tokens are classified:

1. Edit `scripts&#47;ops&#47;validate_docs_token_policy.py`
2. Update the patterns in `DocsTokenPolicyValidator._classify_token()`
3. Add test cases in `tests&#47;ops&#47;test_validate_docs_token_policy.py`
4. Verify all existing docs still pass: `python scripts&#47;ops&#47;validate_docs_token_policy.py --all`

---

## Quick Reference

| Scenario | Action | Example |
|----------|--------|---------|
| Illustrative path | Encode with `&#47;` | `scripts&#47;example.py` |
| Branch name | No encoding (allowed) | `feature&#47;my-branch` |
| Real repo file | No encoding | `scripts&#47;ops&#47;validate_docs_token_policy.py` (if exists) |
| URL | No encoding | ``https:&#47;&#47;github.com&#47;...`` |
| Command | No encoding | `python scripts&#47;run.py` |
| Generic placeholder | Add to allowlist | ``some&#47;path`` |
| Fenced code block | No action needed | (automatically ignored) |

---

## References

- Script: ``scripts&#47;ops&#47;validate_docs_token_policy.py``
- Tests: ``tests&#47;ops&#47;test_validate_docs_token_policy.py``
- Allowlist: ``scripts&#47;ops&#47;docs_token_policy_allowlist.txt``
- CI Workflow: ``.github&#47;workflows&#47;docs-token-policy-gate.yml``
- Related: [Docs Reference Targets False Positives](RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md)

---

**Version:** 1.0  
**Last Updated:** 2026-01-13  
**Owner:** ops
