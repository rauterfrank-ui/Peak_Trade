# Branch Protection: Required Status Checks

**Repository:** `rauterfrank-ui/Peak_Trade`  
**Branch:** `main`  
**Last Updated:** 2025-12-27

---

## Current Required Checks (main)

The following status checks are **required** and must pass before any PR can be merged to `main`:

1. **CI Health Gate (weekly_core)**
2. **Guard tracked files in reports directories**
3. **audit**
4. **tests (3.11)**
5. **strategy-smoke**
6. **Policy Critic Gate**
7. **Lint Gate**
8. **Docs Diff Guard Policy Gate** ⭐ (Added: 2025-12-25)
9. **docs-reference-targets-gate** ⭐ (Added: 2025-12-26)

**Total:** 9 required checks  
**Strict Mode:** `false` (PRs do not need to be up-to-date with base branch)

---

## How to Verify

### List All Required Checks

```bash
OWNER="rauterfrank-ui"
REPO="Peak_Trade"
BRANCH="main"

gh api -H "Accept: application/vnd.github+json" \
  "/repos/${OWNER}/${REPO}/branches/${BRANCH}/protection/required_status_checks" \
  | jq -r '.contexts[]' | nl -ba
```

### Check if Specific Check is Required

```bash
gh api -H "Accept: application/vnd.github+json" \
  "/repos/${OWNER}/${REPO}/branches/${BRANCH}/protection/required_status_checks" \
  | jq -r '.contexts[]' | grep "Docs Diff Guard Policy Gate"
```

**Expected Output:**
```
Docs Diff Guard Policy Gate
```

### Full Branch Protection Details

```bash
gh api -H "Accept: application/vnd.github+json" \
  "/repos/${OWNER}/${REPO}/branches/${BRANCH}/protection/required_status_checks" \
  | jq .
```

---

## Automated Drift Guard

### What is it?

The **Required Checks Drift Guard** automatically verifies that the documented list of required checks (above) matches the live state on GitHub. This prevents documentation drift and ensures branch protection stays in sync.

### How to Use

**Quick check:**
```bash
scripts/ops/verify_required_checks_drift.sh
```

**Integrated check (part of ops_doctor):**
```bash
ops_center.sh doctor
```

### Exit Codes

- `0` = No drift (doc matches live)
- `1` = Drift detected (hard fail)
- `2` = Drift detected (warn-only mode)

### Interpreting Results

**✅ PASS:** Doc and live state match perfectly.

**⚠️ WARN:** Drift detected. The script will show:
- **Missing from Live:** Checks documented but not configured on GitHub
- **Extra in Live:** Checks configured on GitHub but not documented

**Action Required:**
1. Review the diff output
2. Update documentation if live state is correct
3. Or adjust branch protection if doc is correct

### Troubleshooting

**"gh not authenticated":**
```bash
gh auth login
```

**"jq not found":**
```bash
brew install jq
```

**"No checks found in doc":**
- Verify the "Current Required Checks (main)" section exists
- Check numbering format: `1. **Check Name**`

---

## Why This Matters

### Docs Diff Guard Policy Gate

The **Docs Diff Guard Policy Gate** is a critical safeguard that prevents accidental removal or regression of the Docs Diff Guard documentation.

**What it does:**
- Automatically runs on every PR to `main`
- Triggers when changes affect:
  - `docs/ops/` (any files)
  - `scripts/ops/review_and_merge_pr.sh`
  - `scripts/ops/docs_diff_guard.sh`
- Validates presence of the marker `"Docs Diff Guard (auto beim Merge)"` in:
  - `docs/ops/PR_MANAGEMENT_TOOLKIT.md`
  - `docs/ops/PR_MANAGEMENT_QUICKSTART.md`
  - `docs/ops/README.md`

**If validation fails:**
```
❌ Docs Diff Guard Policy: section marker missing in required docs.
   Marker: Docs Diff Guard (auto beim Merge)
   Missing in:
    - docs/ops/README.md

   Fix:
     python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/README.md
```

**When not applicable:**
- Returns `✅ Docs Diff Guard Policy: not applicable (no relevant changes).`
- Exit code 0 (SUCCESS)
- Does not block merge

### Impact of Required Status Checks

Making a check **required** means:
- ✅ **All PRs must pass** before merge
- ❌ **Merge is blocked** if check fails or is missing
- 🔒 **Cannot be bypassed** (unless admin override)
- 📊 **Visible in PR status** (shows as pending/failed/success)

This ensures:
1. **Consistent enforcement** of policies across all PRs
2. **Prevention of regressions** in critical documentation
3. **Auditability** of changes affecting protected areas
4. **Clear remediation** guidance when checks fail

---

## Implementation History

### 2025-12-25: Docs Diff Guard Policy Gate

**PR:** [#318](https://github.com/rauterfrank-ui/Peak_Trade/pull/318)  
**Commit:** `e89dc8c`

**Changes:**
- Added `.github/workflows/docs_diff_guard_policy_gate.yml`
- Added `scripts/ci/check_docs_diff_guard_section.py`
- Added missing section to `docs/ops/README.md`
- Configured as Required Check via GitHub API

**Rationale:**
Completes the Docs Diff Guard feature suite (PR #311-317) by enforcing documentation consistency at the branch protection level. Prevents accidental removal of critical documentation sections.

**Verification (Drill PR #319):**
- ✅ Check appears on all PRs
- ✅ Correctly identifies "not applicable" scenarios
- ✅ Returns SUCCESS (exit 0) when not triggered
- ✅ Does not block unrelated PRs

---

## Adding a New Required Check

### Prerequisites

1. The check must have run at least once in the last ~7 days
2. You need admin permissions on the repository
3. The check name must match exactly (case-sensitive)

### Steps

```bash
cd ~/Peak_Trade

OWNER="rauterfrank-ui"
REPO="Peak_Trade"
BRANCH="main"
NEW_CTX="Your Check Name Here"

# 1. Get current checks
cur="$(gh api -H "Accept: application/vnd.github+json" \
  "repos/$OWNER/$REPO/branches/$BRANCH/protection/required_status_checks")"

# 2. Build update payload
payload="$(echo "$cur" | jq --arg ctx "$NEW_CTX" '{
  strict: .strict,
  contexts: ((.contexts // []) + [$ctx] | unique | sort)
}')"

# 3. Apply update
tmp="$(mktemp)"
echo "$payload" > "$tmp"
gh api -X PATCH -H "Accept: application/vnd.github+json" \
  "repos/$OWNER/$REPO/branches/$BRANCH/protection/required_status_checks" \
  --input "$tmp"
rm -f "$tmp"

# 4. Verify
gh api -H "Accept: application/vnd.github+json" \
  "repos/$OWNER/$REPO/branches/$BRANCH/protection/required_status_checks" \
  | jq -r '.contexts[]'
```

### Idempotency

The command is idempotent - running it multiple times with the same check name will not create duplicates due to `unique | sort` in the jq pipeline.

---

## Related Documentation

- **Docs Diff Guard Implementation:** `docs/ops/README.md` (Section: "Docs Diff Guard")
- **PR Management Toolkit:** `docs/ops/PR_MANAGEMENT_TOOLKIT.md`
- **CI Policy Script:** `scripts/ci/check_docs_diff_guard_section.py`
- **Workflow:** `.github/workflows/docs_diff_guard_policy_gate.yml`
- **Merge Logs:** Docs Diff Guard implementation series (PR #311-317)

---

## Maintenance

### When to Update This Document

- ✅ When adding/removing required checks
- ✅ When changing strict mode setting
- ✅ After significant branch protection changes
- ✅ When deprecating/replacing existing checks

### Verification Schedule

Run verification commands:
- **After branch protection changes:** Immediately
- **During quarterly audits:** Every 3 months
- **Before major releases:** As part of release checklist

---

## Notes

- **App ID 15368:** GitHub Actions (all current checks use this)
- **Contexts vs Checks:** Legacy "contexts" field and new "checks" field contain the same data
- **Case Sensitivity:** Check names are case-sensitive in API calls
- **Webhook Events:** Required check changes do not trigger webhook events; verification must be manual
