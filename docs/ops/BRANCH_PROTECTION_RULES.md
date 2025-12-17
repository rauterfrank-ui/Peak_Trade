# Branch Protection Rules for Peak_Trade

## Recommended Branch Protection Settings for `main`

This document describes the recommended branch protection rules for the `main` branch to ensure code quality and prevent accidental issues.

### Required Status Checks

Enable "Require status checks to pass before merging" and select the following workflows:

**TIER 1: Fast Gates (Critical)**
- ✅ `Lint` - Code quality and formatting
- ✅ `Security / dependency-scan` - Dependency vulnerability scanning
- ✅ `Security / secret-scan` - Secret scanning

**TIER 2: Core CI (Critical)**
- ✅ `CI - Unit Tests / unit-tests (3.10)` - Unit tests on Python 3.10
- ✅ `CI - Unit Tests / unit-tests (3.11)` - Unit tests on Python 3.11
- ✅ `CI - Unit Tests / unit-tests (3.12)` - Unit tests on Python 3.12
- ✅ `CI - Integration Tests / integration-tests` - Integration tests and RL contract validation
- ✅ `CI - Strategy Smoke Tests / strategy-smoke` - Strategy smoke tests

**TIER 3: Deep Validation (Important)**
- ✅ `Audit / audit` - PR report validation and audit checks

**Existing Workflows (Keep as required)**
- ✅ `Guard reports/ must be ignored` - Ensures generated artifacts are not committed
- ✅ Other existing workflow checks as appropriate

### Additional Protection Settings

#### Require branches to be up to date
- ✅ **Enable**: Ensure branches are up to date before merging
  - Prevents merge conflicts and ensures tests run against latest code

#### Require conversation resolution
- ✅ **Enable**: All conversations must be resolved before merging
  - Ensures all review comments are addressed

#### Require pull request reviews
- **Recommended**: At least 1 approving review
- **Optional**: Dismiss stale pull request approvals when new commits are pushed

#### Restrict pushes
- ✅ **Enable**: Only allow specific people, teams, or apps to push
  - Prevents accidental direct pushes to main
  - All changes must go through pull requests

#### Do not allow force pushes
- ✅ **Enable**: Prevent force pushes to main
  - Preserves git history
  - Prevents accidental loss of commits

#### Do not allow deletion
- ✅ **Enable**: Prevent deletion of the main branch

#### Require linear history (Optional)
- **Optional**: Enforce linear commit history
  - Requires merge commits or rebase merging
  - Makes history easier to follow
  - **Note**: May require adjusting team workflow

### Implementation Steps

1. Navigate to: Repository → Settings → Branches
2. Click "Add rule" for `main` branch
3. Configure the settings above
4. Click "Create" or "Save changes"

### Testing Branch Protection

After enabling branch protection:

1. Create a test branch
2. Make a change and open a PR
3. Verify all status checks appear
4. Verify you cannot merge until checks pass
5. Verify you cannot push directly to main

### Troubleshooting

**Issue**: Status checks not appearing
- **Solution**: Ensure workflows have run at least once. Push to a branch or manually trigger workflows.

**Issue**: Cannot merge even though checks pass
- **Solution**: Check if branch is up to date. Rebase or merge main into your branch.

**Issue**: Too many required checks
- **Solution**: Start with TIER 1 and TIER 2 only, add TIER 3 later as team adapts.

### Notes

- Status checks may take up to a few minutes to register after initial workflow runs
- You can temporarily disable branch protection in emergencies (requires admin access)
- Review and update these rules periodically as the project evolves
