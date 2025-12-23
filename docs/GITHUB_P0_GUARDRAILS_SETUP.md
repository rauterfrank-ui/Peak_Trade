# Peak Trade P0 Guardrails Setup Guide

This guide documents the required GitHub repository settings to activate P0 Guardrails for the Peak_Trade repository. These settings must be configured through the GitHub web UI or API by a repository administrator.

## Table of Contents
1. [Branch Protection Rules / Rulesets](#1-branch-protection-rules--rulesets)
2. [Merge Queue](#2-merge-queue)
3. [Security Features](#3-security-features)
4. [Merge Policy](#4-merge-policy)
5. [Verification](#5-verification)

---

## 1. Branch Protection Rules / Rulesets

**Path:** Repository → Settings → Branches → Branch protection rules (or Rulesets)

### For `main` branch:

#### Required Status Checks
Configure the following status checks that must pass before merging:

- ✅ **tests (3.11)** - From CI workflow, Python 3.11 test suite
- ✅ **lint** - From Lint workflow, ruff linter checks
- ✅ **strategy-smoke** - From CI workflow, strategy smoke tests
- ✅ **Policy Critic Review** (policy-review) - From Policy Critic Gate workflow
- ✅ **format-only-verifier** - From Policy Critic Gate workflow

**Additional CI checks to consider:**
- Guard tracked files
- CI Health Gate
- deps_sync_guard
- audit

#### Branch Protection Settings

1. **Require a pull request before merging** ✅
   - Required number of approvals: **1** (minimum, **2** recommended for critical paths)
   - Dismiss stale pull request approvals when new commits are pushed: ✅ (recommended)
   - Require review from Code Owners: ✅ (recommended, requires CODEOWNERS file)

2. **Require status checks to pass before merging** ✅
   - Require branches to be up to date before merging: ✅ **CRITICAL for Merge Queue**
   - Status checks that are required:
     - `tests (3.11)`
     - `lint`
     - `strategy-smoke`
     - `policy-review`
     - `format-only-verifier`
     - Any other "must pass" checks from your CI

3. **Require conversation resolution before merging** ✅
   - All PR review comments must be resolved

4. **Restrict who can push to matching branches** ⚠️ (Optional but recommended)
   - Only allow specific users/teams to push directly to main
   - Forces all changes through PR workflow

5. **Allow force pushes** ❌ (Should be disabled)
   - Prevents history rewriting on main

6. **Allow deletions** ❌ (Should be disabled)
   - Prevents branch deletion

### Using Rulesets (Recommended for newer repos)

If using Rulesets instead of classic Branch Protection Rules:

**Path:** Repository → Settings → Rules → Rulesets → New ruleset → New branch ruleset

1. **Ruleset Name:** `main-branch-protection`
2. **Enforcement status:** Active
3. **Target branches:** `main` (or use `refs/heads/main`)
4. **Rules:**
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass
   - ✅ Require conversation resolution
   - ✅ Block force pushes
   - ⚠️ Restrict deletions

---

## 2. Merge Queue

**Path:** Repository → Settings → Branches → Merge queue

### Configuration Steps:

1. **Enable merge queue for `main` branch** ✅

2. **Merge method in queue:**
   - Recommended: **Squash and merge**
   - Alternative: **Merge commit** (if you want to preserve PR structure)

3. **Queue settings:**
   - **Merge method:** Squash and merge
   - **Build concurrency:** 1 (start conservative, increase if needed)
   - **Minimum pull requests to merge together:** 1
   - **Maximum pull requests to merge together:** 5
   - **Merge queue merge method:** Same as PR merge method

4. **Status checks required for merge queue:**
   - All the same checks as branch protection:
     - `tests (3.11)`
     - `lint`
     - `strategy-smoke`
     - `policy-review`
     - `format-only-verifier`

### Important Notes:

⚠️ **Workflow Support:** The following workflows have been updated to support `merge_group` trigger:
- `.github/workflows/ci.yml`
- `.github/workflows/lint.yml`
- `.github/workflows/policy_critic.yml`

This means these workflows will run when PRs are added to the merge queue, not just on pull_request events.

---

## 3. Security Features

**Path:** Repository → Settings → Code security and analysis

### Required Security Settings:

1. **Dependency graph** ✅
   - Status: Enabled
   - Automatically enabled for public repos, must be enabled for private repos

2. **Dependabot alerts** ✅
   - Status: Enabled
   - Automatically receive alerts for vulnerable dependencies

3. **Dependabot security updates** ✅ (Recommended)
   - Status: Enabled
   - Automatically opens PRs to update vulnerable dependencies

4. **Secret scanning** ✅
   - Status: Enabled
   - Scans repository for known secret patterns
   - Available for public repos, requires GitHub Advanced Security for private repos

5. **Push protection** ✅
   - Status: Enabled
   - Blocks pushes that contain secrets
   - Requires Secret scanning to be enabled

6. **Code scanning** ✅
   - Tool: **CodeQL** (GitHub's semantic code analysis engine)
   - Status: Enabled
   - Configuration:
     - **Default setup** (recommended) or **Advanced setup** (for custom queries)
     - Schedule: On push to default branch and on pull requests
     - Languages: Python (automatically detected)

### CodeQL Setup (if not already configured):

**Path:** Repository → Settings → Code security and analysis → Code scanning → Set up → CodeQL analysis

1. Choose **Default** for automatic configuration
2. Or choose **Advanced** to use a custom workflow file
3. Query suites: **Default** (or **Extended** for more thorough analysis)
4. Languages: Python
5. Events: `push`, `pull_request`, `merge_group`

---

## 4. Merge Policy

**Path:** Repository → Settings → General → Pull Requests

### Recommended Settings:

1. **Allow merge commits** ❌ (Optional - disable if you want squash-only)

2. **Allow squash merging** ✅ **RECOMMENDED**
   - Default commit message: `Pull request title and description`
   - This is the recommended merge method for clean history

3. **Allow rebase merging** ❌ (Optional - can be enabled if team prefers)

4. **Automatically delete head branches** ✅ **RECOMMENDED**
   - Cleans up PR branches after merge
   - Keeps repository tidy

5. **Allow auto-merge** ✅ (Optional but useful)
   - PRs can be set to auto-merge when all checks pass
   - Works well with merge queue

---

## 5. Verification

After configuring all settings, verify the setup:

### Terminal Verification (Local):

```bash
# 1. Check GitHub CLI authentication
gh auth status

# 2. View repository in browser
gh repo view --web

# 3. View current branch protection rules
gh api repos/:owner/:repo/branches/main/protection | jq '.'

# 4. Check a specific PR's status checks (replace <NUM> with PR number)
gh pr checks <NUM> --watch
```

### GitHub UI Verification:

1. **Branch Protection:**
   - Go to Settings → Branches
   - Verify `main` branch has protection rules
   - Check that all required status checks are listed

2. **Merge Queue:**
   - Go to Settings → Branches
   - Verify merge queue is enabled for `main`
   - Check queue settings match recommendations

3. **Security:**
   - Go to Settings → Code security and analysis
   - Verify all security features show "Enabled"
   - Check Security tab for any existing alerts

4. **CODEOWNERS:**
   - File location: `.github/CODEOWNERS`
   - Verify syntax: `cat .github/CODEOWNERS`
   - GitHub will show code owners in PR review section

### Test with a PR:

1. Create a test PR that modifies a file in a protected path (e.g., `src/governance/`)
2. Verify:
   - ✅ Required reviewers are automatically requested (from CODEOWNERS)
   - ✅ Status checks appear and run
   - ✅ Cannot merge until checks pass and approvals received
   - ✅ Conversations must be resolved before merge
   - ✅ Merge queue is available (if enabled)

---

## Summary Checklist

Before going live with P0 Guardrails, confirm:

### Branch Protection ✅
- [ ] Require PR before merging (main)
- [ ] Require 1-2 approvals
- [ ] Require status checks: tests (3.11), lint, strategy-smoke, policy-review
- [ ] Require branches up to date before merging
- [ ] Require conversation resolution
- [ ] (Optional) Restrict who can push to main

### Merge Queue ✅
- [ ] Enabled for main branch
- [ ] Workflows support `merge_group` trigger
- [ ] Same status checks as branch protection

### Security ✅
- [ ] Dependency graph: ON
- [ ] Dependabot alerts: ON
- [ ] Secret scanning: ON
- [ ] Push protection: ON
- [ ] Code scanning (CodeQL): ON

### Merge Policy ✅
- [ ] Merge method: Squash (or team preference)
- [ ] Auto-delete branches: ON

### Code Ownership ✅
- [ ] `.github/CODEOWNERS` file created
- [ ] Paths covered: src/governance/, src/risk/, src/live/, src/execution/, scripts/ops/
- [ ] Team handles or usernames configured

### Verification ✅
- [ ] Test PR created and verified
- [ ] Status checks run correctly
- [ ] Merge queue works (if enabled)
- [ ] Code owners are notified
- [ ] Security scanning is active

---


<!-- SOLO_MODE_SECTION_START -->
## Solo Mode (1 Maintainer) — kein Self-Approval Deadlock

Wenn du **allein** am Repo arbeitest, kann ein PR-Autor seinen eigenen PR **nicht** als Approval zählen lassen.
Ein Setup mit „Require approvals" + „Require review from Code Owners" führt deshalb zu einem **Deadlock**.

### Empfohlene Guardrails für Solo-Workflow

Behalte die **harten** Schutzmechanismen bei, die solo wirklich zählen:

- ✅ **PR-Workflow erzwingen** (kein Direct Push auf `main`)
- ✅ **Required Status Checks** als Merge-Blocker (inkl. automatisierter Policy-Checks)
- ✅ **Admin Enforcement** aktiv
- ✅ **Force Pushes** verboten
- ✅ **Branch Deletions** verboten

Und deaktiviere die manuellen Review-Gates, die solo nicht erfüllbar sind:

- ✅ `required_approving_review_count: 0`
- ✅ `require_code_owner_reviews: false`
- (optional) `dismiss_stale_reviews: false` (weil keine Reviews erforderlich)

> **Hinweis zu CODEOWNERS:**  
> In Solo Mode dient `.github/CODEOWNERS` als **Ownership-Markierung / Dokumentation** (kritische Pfade sind sichtbar),
> aber nicht als manuelles Merge-Gate.

### Empfohlene Required Status Checks (Solo Mode)

Verwende **nur** Checks, die bei jedem PR laufen (ohne Path-Filter):

```json
{
  "required_status_checks": {
    "strict": false,
    "contexts": [
      "CI Health Gate (weekly_core)",
      "Guard tracked files in reports directories",
      "audit",
      "tests (3.11)",
      "strategy-smoke"
    ]
  }
}
```

⚠️ **Wichtig:** Checks mit Path-Filtern (z.B. `Policy Critic Review`, `lint`) sollten NICHT als Required gesetzt werden,
da sie bei Docs-only PRs nicht laufen und den Merge blockieren würden.

### Source of Truth / Verifikation (CLI)

Branch-Protection-Status:
```bash
gh api repos/OWNER/REPO/branches/main/protection
```

Required Status Checks:
```bash
gh api repos/OWNER/REPO/branches/main/protection/required_status_checks
```

Pull Request Reviews:
```bash
gh api repos/OWNER/REPO/branches/main/protection/required_pull_request_reviews
```

### Beispiel: Branch Protection via API setzen (Solo Mode)

```bash
OWNER="your-username"
REPO="your-repo"
BRANCH="main"

gh api -X PUT "repos/$OWNER/$REPO/branches/$BRANCH/protection" --input - <<'JSON'
{
  "required_status_checks": {
    "strict": false,
    "contexts": [
      "CI Health Gate (weekly_core)",
      "Guard tracked files in reports directories",
      "audit",
      "tests (3.11)",
      "strategy-smoke"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "require_code_owner_reviews": false,
    "dismiss_stale_reviews": false
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
```

### Validierung

Nach dem Setup sollte ein Test-PR:
1. ✅ Direkten Push auf `main` blockieren
2. ✅ Alle Required Status Checks durchlaufen
3. ✅ Ohne manuelle Approval mergbar sein (wenn alle Checks grün)
4. ✅ Admin-Regeln durchsetzen (auch für Admins gültig)

Siehe auch: `docs/ENFORCEMENT_DRILL_REPORT.md` für ein vollständiges Validierungsbeispiel.

<!-- SOLO_MODE_SECTION_END -->

---
## Additional Resources

- [GitHub Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [GitHub Merge Queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)
- [GitHub Code Owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [GitHub CodeQL](https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/about-code-scanning-with-codeql)

---

## Notes

- Most settings require repository **admin** permissions
- Some security features (Secret scanning push protection, Code scanning) require **GitHub Advanced Security** for private repositories
- The `.github/CODEOWNERS` file and workflow updates have been committed to support these guardrails
- Team handles in CODEOWNERS should be replaced with actual GitHub usernames or team names (format: `@org/team-name` or `@username`)

---

**Status:** Ready for implementation by repository administrator
**Date:** 2025-12-23
**Version:** 1.0
