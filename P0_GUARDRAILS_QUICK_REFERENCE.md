# P0 Guardrails Quick Reference

## What Was Implemented (Code Changes)

### ✅ 1. CODEOWNERS File
**File:** `.github/CODEOWNERS`

Critical paths now require review from designated code owners:
- `/src/governance/` → Trading policies, risk rules, compliance
- `/src/risk/` → Risk models, position sizing, drawdown protection
- `/src/live/` → Real money execution, live strategy deployment
- `/src/execution/` → Order execution, exchange integration
- `/scripts/ops/` → Production operations, deployment

**Action Required:** Replace placeholder team handles (e.g., `@rauterfrank-ui/governance-reviewers`) with actual GitHub usernames or team names.

### ✅ 2. Merge Queue Support
**Files Modified:**
- `.github/workflows/ci.yml`
- `.github/workflows/lint.yml`
- `.github/workflows/policy_critic.yml`
- `.github/workflows/audit.yml`
- `.github/workflows/deps_sync_guard.yml`
- `.github/workflows/test_health.yml`
- `.github/workflows/guard-reports-ignored.yml`
- `.github/workflows/policy_tracked_reports_guard.yml`

All critical workflows (8 total) now support the `merge_group` trigger, which is required for GitHub Merge Queue functionality.

### ✅ 3. Setup Documentation
**File:** `docs/GITHUB_P0_GUARDRAILS_SETUP.md`

Comprehensive guide covering:
- Branch protection rules configuration
- Merge queue setup
- Security features activation
- Merge policy settings
- Verification steps

---

## What Requires GitHub UI Configuration

The following settings **cannot be configured via code** and require repository administrator access through the GitHub web interface:

### 🔧 1. Branch Protection Rules (Settings → Branches)

For `main` branch, configure:
- ✅ Require pull request before merging (1-2 approvals)
- ✅ Require status checks to pass:
  - `tests (3.11)`
  - `lint`
  - `strategy-smoke`
  - `policy-review`
  - `format-only-verifier`
  - `audit` (recommended)
  - `guard-no-tracked-reports` (recommended)
  - `deps_sync_guard` (recommended)
  - `test_health` (optional)
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ⚠️ (Optional) Restrict who can push to main

### 🔧 2. Merge Queue (Settings → Branches → Merge queue)

- ✅ Enable merge queue for main branch
- ✅ Configure merge method: Squash (recommended)
- ✅ Set build concurrency: 1 (conservative start)

### 🔧 3. Security Features (Settings → Code security and analysis)

- ✅ Secret scanning: ON
- ✅ Push protection: ON
- ✅ Dependency graph: ON
- ✅ Dependabot alerts: ON
- ✅ Code scanning (CodeQL): ON

### 🔧 4. Merge Policy (Settings → General → Pull Requests)

- ✅ Allow squash merging: ON (recommended)
- ✅ Automatically delete head branches: ON
- ⚠️ Disable other merge methods (optional, for consistency)

---

## Verification Checklist

After configuring GitHub UI settings:

```bash
# 1. Check GitHub CLI authentication
gh auth status

# 2. View repository settings
gh repo view --web

# 3. Check branch protection rules
gh api repos/:owner/:repo/branches/main/protection | jq '.'

# 4. Test with a PR
gh pr create --title "Test P0 Guardrails" --body "Testing branch protection and merge queue"
gh pr checks <NUM> --watch
```

Manual verification:
1. Create a test PR that modifies a file in `src/governance/` or another protected path
2. Verify code owners are automatically requested for review
3. Verify all required status checks run
4. Verify cannot merge until checks pass and approvals received
5. Verify merge queue is available (if enabled)

---

## Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| CODEOWNERS | ✅ Created | Team handles need updating with real usernames |
| Workflow merge_group | ✅ Added | 8 workflows updated (ci, lint, policy_critic, audit, deps_sync, test_health, guards) |
| Setup Guide | ✅ Created | See docs/GITHUB_P0_GUARDRAILS_SETUP.md |
| Branch Protection | ⏳ Pending | Requires GitHub UI configuration |
| Merge Queue | ⏳ Pending | Requires GitHub UI configuration |
| Security Features | ⏳ Pending | Requires GitHub UI configuration |
| Merge Policy | ⏳ Pending | Requires GitHub UI configuration |

---

## Next Steps (Priority Order)

1. **Review this PR** and the setup guide
2. **Update CODEOWNERS** with actual GitHub usernames/teams
3. **Configure Branch Protection** rules via GitHub UI (highest priority)
4. **Enable Security Features** (Secret scanning, CodeQL, etc.)
5. **Configure Merge Queue** (requires branch protection first)
6. **Set Merge Policy** (Squash merge, auto-delete branches)
7. **Test thoroughly** with a real PR before relying on guardrails

---

## Important Notes

⚠️ **Repository Admin Required:** All GitHub UI configurations require repository administrator permissions.

⚠️ **Private Repo Limitations:** Some security features (Secret scanning push protection, Code scanning) may require **GitHub Advanced Security** license for private repositories.

⚠️ **Team Setup:** If using team handles in CODEOWNERS (e.g., `@org/team-name`), ensure those teams exist in your GitHub organization first.

⚠️ **Testing:** Always test guardrails with a non-critical PR before relying on them for production protection.

---

**For detailed instructions, see:** `docs/GITHUB_P0_GUARDRAILS_SETUP.md`

**Date:** 2025-12-23  
**PR:** Activate Peak_Trade P0 Guardrails
