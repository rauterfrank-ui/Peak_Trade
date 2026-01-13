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

**Solution:** Encode the forward slash (`/`) as `&#47;` in illustrative paths, while leaving real repo targets, URLs, commands, and branch names unchanged.

---

## When This Gate Triggers

The gate scans changed Markdown files (`.md`) for inline-code tokens (single backticks: `` `token` ``) containing `/` and enforces:

1. **ILLUSTRATIVE** paths (e.g., `scripts&#47;fake.py`, `config&#47;example.toml`) → **MUST** use `&#47;` encoding
2. **REAL_REPO_TARGET** (existing files) → **NO** encoding required
3. **BRANCH_NAME** patterns (e.g., `feature/my-feature`, `docs/update`) → **NO** encoding required
4. **URL** (http/https) → **NO** encoding required
5. **COMMAND** (prefixed with `python `, `git `, etc.) → **NO** encoding required
6. **LOCAL_PATH** (starts with `./`, `../`, `~/`, or `/`) → **NO** encoding required
7. **ALLOWLISTED** tokens → **NO** encoding required

---

## Classification Examples

| Token | Classification | Encoding Required? | Reason |
|-------|----------------|-------------------|--------|
| `scripts&#47;example.py` | ENCODED | ✅ Already compliant | Forward slash already encoded |
| (See fenced block below) | ILLUSTRATIVE | ❌ **VIOLATION** | Looks like path but doesn't exist |
| `scripts&#47;real_script.py` | REAL_REPO_TARGET (if exists) | ✅ Compliant | File exists in repo |
| `feature/my-feature` | BRANCH_NAME | ✅ Compliant | Branch name pattern (known prefix) |
| `docs/update` | BRANCH_NAME | ✅ Compliant | Branch name pattern (known prefix) |
| `python scripts/run.py` | COMMAND | ✅ Compliant | Command prefix detected |
| `https://example.com/path` | URL | ✅ Compliant | URL detected |
| `./scripts/local.py` | LOCAL_PATH | ✅ Compliant | Local path prefix |
| `some/path` | ILLUSTRATIVE (if allowlisted) | ✅ Compliant | In allowlist |

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
  Line 15: `scripts/example.py` (ILLUSTRATIVE)
    → Illustrative path token must use &#47; encoding
    💡 Replace `scripts/example.py` with `scripts&#47;example.py`

  Line 23: `feature/my-branch` (BRANCH_NAME)
    → Illustrative path token must use &#47; encoding
    💡 Replace `feature/my-branch` with `feature&#47;my-branch`
```

### Step 2: Apply the Fix

**Option A: Manual Fix**

Replace the forward slash with `&#47;` inside the inline-code span:

```diff
- Here's an example: `scripts/example.py`.
+ Here's an example: `scripts&#47;example.py`.

- Checkout branch: `feature/my-branch`.
+ Checkout branch: `feature&#47;my-branch`.
```

**Option B: Automated Fix (Python Script)**

```bash
# Run validator to detect violations
python scripts/ops/validate_docs_token_policy.py

# Fix automatically (if you have a fix script)
# Or use sed/rg to replace specific tokens
```

**Option C: Add to Allowlist (If Appropriate)**

If a token is a generic placeholder (e.g., `some/path`) used across many docs:

1. Add it to `scripts/ops/docs_token_policy_allowlist.txt`:

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
   ✅ `scripts/run_backtest.py` (if file exists)
   ```

2. **URLs**:
   ```markdown
   ✅ `https://github.com/user/repo/blob/main/file.py`
   ```

3. **Commands** with path arguments:
   ```markdown
   ✅ `python scripts/run.py`
   ✅ `git diff origin/main`
   ```

4. **Local path patterns**:
   ```markdown
   ✅ `./scripts/local.py`
   ✅ `../config/file.toml`
   ✅ `~/Documents/file.txt`
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
`scripts/example.py` (gate thinks this is a missing file)

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

### Updating the Allowlist

The allowlist is at `scripts/ops/docs_token_policy_allowlist.txt`.

**When to add entries:**
- Generic placeholders used in tutorials (e.g., `some/path`)
- Common system paths (e.g., `/usr/local/bin`)
- Third-party paths (e.g., `/var/log`)

**When NOT to add entries:**
- Project-specific illustrative paths (use `&#47;` encoding instead)
- One-off examples in a single doc

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
| Branch name | No encoding (allowed) | `feature/my-branch` |
| Real repo file | No encoding | `scripts&#47;ops&#47;validate_docs_token_policy.py` (if exists) |
| URL | No encoding | `https://github.com/...` |
| Command | No encoding | `python scripts/run.py` |
| Generic placeholder | Add to allowlist | `some/path` |
| Fenced code block | No action needed | (automatically ignored) |

---

## References

- Script: `scripts/ops/validate_docs_token_policy.py`
- Tests: `tests/ops/test_validate_docs_token_policy.py`
- Allowlist: `scripts/ops/docs_token_policy_allowlist.txt`
- CI Workflow: `.github/workflows/docs-token-policy-gate.yml`
- Related: [Docs Reference Targets False Positives](RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md)

---

**Version:** 1.0  
**Last Updated:** 2026-01-13  
**Owner:** ops
