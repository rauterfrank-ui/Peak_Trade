# PR Template Selection Guide

**Audience:** Peak_Trade Operators & Contributors  
**Purpose:** How to select the correct PR template for your change type

---

## Available PR Templates

### 1. workflow_changes.md

**Use for:** Workflow / CI Configuration Changes

**Triggers:**
- Any changes to files in .github/workflows/
- Modifications to GitHub Actions workflows
- Changes to CI/CD pipeline configuration
- Updates to required status checks
- Path filter modifications

**Risk Level:** HIGH (Governance Surface)

**Key Features:**
- Risk assessment checklist
- Gate safety verification
- Required checks impact analysis
- Rollback plan requirement
- Ops reviewer checklist

---

## How to Select a Template

### Method 1: GitHub Web UI (Automatic)

When creating a PR via GitHub UI:

1. Navigate to your repository on GitHub
2. Click "Pull requests" tab
3. Click "New pull request"
4. Select your branch
5. Click "Create pull request"
6. GitHub will show available templates in a dropdown or link

**Note:** If you have multiple templates, GitHub shows a template chooser automatically.

---

### Method 2: Direct URL with Query Parameter

Add the template query parameter to your PR creation URL:

**Format:**

```
https://github.com/OWNER/REPO/compare/BASE...HEAD?template=TEMPLATE_NAME
```

**Example for workflow changes:**

```
https://github.com/YOUR_ORG/Peak_Trade/compare/main...feature-branch?template=workflow_changes.md
```

**Steps:**

1. Replace YOUR_ORG with your GitHub organization
2. Replace feature-branch with your actual branch name
3. Keep template=workflow_changes.md for workflow PRs

---

### Method 3: Using gh CLI

If you use GitHub CLI:

```bash
# Create PR with specific template (requires manual template selection in editor)
gh pr create --web

# Or: Create PR and manually paste template content
gh pr create --title "Your Title" --body "$(cat .github/PULL_REQUEST_TEMPLATE/workflow_changes.md)"
```

**Note:** The gh CLI will open your browser where you can select templates.

---

## Template Selection Decision Tree

```
Is your PR changing files in .github/workflows/?
├─ YES → Use workflow_changes.md template
└─ NO  → Use default PR template (if available) or GitHub's standard form
```

**Future Templates (Planned):**
- policy_changes.md - For policy pack modifications
- runbook_changes.md - For operational runbook updates
- docs_major.md - For major documentation refactors

---

## Testing Template Selection Locally

Before creating a PR, preview the template:

```bash
# View the template
cat .github/PULL_REQUEST_TEMPLATE/workflow_changes.md

# Or open in your editor
code .github/PULL_REQUEST_TEMPLATE/workflow_changes.md
```

---

## Governance Notes

### Why Templates Matter

PR templates enforce:
- Consistent risk assessment
- Gate safety verification
- Rollback planning
- Scope discipline

### Required Fields

Templates with "Required Review" sections MUST be filled out completely before requesting approval.

### Bypassing Templates (Discouraged)

You can create a PR without a template by:
- Using the GitHub API directly
- Deleting template content after PR creation

**WARNING:** Bypassing templates for high-risk changes (workflows, policies) may result in:
- PR rejection by reviewers
- Failed gate checks
- Merge blocks

---

## Troubleshooting

### Template Not Showing Up

**Problem:** GitHub doesn't show template chooser

**Solutions:**

1. Check file location - must be in .github/PULL_REQUEST_TEMPLATE/
2. Check file extension - must be .md
3. Check repository settings - templates may be disabled
4. Use direct URL method as fallback

### Multiple Templates Conflict

**Problem:** Not sure which template to use

**Solution:**

1. If changes include workflows → workflow_changes.md takes precedence
2. If mixed changes → use the highest-risk template
3. When in doubt → ask in project chat or use workflow_changes.md (most comprehensive)

### Template Fields Don't Apply

**Problem:** Template has sections that don't apply to your PR

**Solution:**

1. Mark sections as N/A with brief justification
2. Check all relevant checkboxes
3. Don't delete sections - mark as "Not applicable: [reason]"

---

## Quick Reference

| Change Type | Template | Risk Level | Required Reviewers |
|-------------|----------|------------|-------------------|
| Workflow/CI | workflow_changes.md | HIGH | Ops + Gate Guardian |
| Policy Pack | (future) | HIGH | Policy Reviewer + Ops |
| Code | (default) | MEDIUM | Code Owner |
| Docs | (default) | LOW | Any Reviewer |
| Runbook | (future) | MEDIUM | Ops |

---

## Additional Resources

**Related Documentation:**
- Peak_Trade Governance Rules
- CI/CD Gate Documentation
- Branch Protection Settings
- Required Checks Configuration

**Runbooks:**
- Check docs/ops/runbooks/ for operational procedures
- See docs/ops/merge_logs/ for PR merge history

---

**Last Updated:** 2026-01-14  
**Maintainer:** Peak_Trade Ops Team  
**Feedback:** Open an issue or discuss in project chat
