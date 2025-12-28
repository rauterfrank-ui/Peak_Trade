# Verified Merge Log PR Script

## Overview

`scripts/create_verified_merge_log_pr.sh` is an **idempotent, reusable script** for creating verified merge log PRs after a feature PR is merged to main.

## Usage

### Basic

```bash
./scripts/create_verified_merge_log_pr.sh <PR_NUMBER>
```

### With Options

```bash
./scripts/create_verified_merge_log_pr.sh <PR_NUMBER> [--base BRANCH] [--branch BRANCH]
```

**Options:**
- `--base BRANCH` - Base branch (default: `main`)
- `--branch BRANCH` - Target branch name (default: `docs/merge-log-pr-<NUM>`)

### Examples

```bash
# Create merge log PR for PR #418
./scripts/create_verified_merge_log_pr.sh 418

# Custom base branch
./scripts/create_verified_merge_log_pr.sh 420 --base develop

# Custom branch name
./scripts/create_verified_merge_log_pr.sh 422 --branch docs/merge-log-custom
```

## What It Does

1. **Validates PR State**
   - Checks if target PR is merged
   - Exits with clear message if not merged yet

2. **Checks for Existing PR**
   - Looks for existing merge-log PR from same branch
   - If found (open or merged), exits gracefully
   - **Idempotent:** Running twice has no negative effects

3. **Generates Merge Log**
   - Creates `docs/ops/PR_<NUM>_MERGE_LOG.md`
   - Includes PR metadata, commits, files changed
   - If file exists with content, keeps it

4. **Updates README**
   - Patches `docs/ops/README.md` under "## Verified Merge Logs"
   - Adds entry: `- **PR #<NUM>** → docs/ops/PR_<NUM>_MERGE_LOG.md`
   - Skips if entry already exists

5. **Creates PR**
   - Commits changes
   - Pushes branch (with force-with-lease)
   - Creates PR titled: "docs(ops): add verified merge log for PR #<NUM>"

## Idempotency Features

### Branch Handling
- **Local branch exists:** Checks out and resets to base
- **Remote branch exists:** Fetches, checks out, resets to latest base
- **Neither exists:** Creates new branch

### File Handling
- **Merge log exists with content (>500 bytes):** Keeps existing
- **README entry exists:** Skips patching
- **No changes to commit:** Exits gracefully (no commit, no PR)

### PR Handling
- **PR exists (open):** Exits with link, suggests waiting for review
- **PR exists (merged):** Exits with success message
- **No PR exists:** Creates new PR

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (PR created or already exists) |
| 1 | Error (missing deps, git issues, etc.) |
| 2 | Target PR not merged yet (retry after merge) |

## Example Runs

### First Run (Success)

```bash
$ ./scripts/create_verified_merge_log_pr.sh 420

🔍 Preflight checks...
✅ All dependencies available

🔍 Checking PR #420 state...
✅ PR #420 is merged: 2025-12-29T10:30:00Z
   feat: some awesome feature
   https://github.com/org/repo/pull/420

🔍 Checking for existing merge-log PR from branch 'docs/merge-log-pr-420'...
✅ No existing PR found - will create new one

📥 Syncing base branch 'main'...
✅ Base branch synced

🌿 Handling branch 'docs/merge-log-pr-420'...
✅ Creating new branch

📝 Generating merge log content...
✅ Generated: docs/ops/PR_420_MERGE_LOG.md
   Size: 1850 bytes

📝 Patching docs/ops/README.md...
✅ Added PR #420 to docs/ops/README.md

🔍 Checking for changes...

📊 Changes to commit:
 A docs/ops/PR_420_MERGE_LOG.md
 M docs/ops/README.md

💾 Committing changes...
✅ Changes committed

📤 Pushing branch 'docs/merge-log-pr-420'...
✅ Branch pushed

🎯 Creating PR...
https://github.com/org/repo/pull/421

✅ Done! Merge log PR created.

📋 Next steps:
   - Review: gh pr view --web
   - Enable auto-merge: gh pr merge --auto --squash --delete-branch
```

### Second Run (Idempotent)

```bash
$ ./scripts/create_verified_merge_log_pr.sh 420

🔍 Preflight checks...
✅ All dependencies available

🔍 Checking PR #420 state...
✅ PR #420 is merged: 2025-12-29T10:30:00Z
   feat: some awesome feature
   https://github.com/org/repo/pull/420

🔍 Checking for existing merge-log PR from branch 'docs/merge-log-pr-420'...
✅ Merge-log PR already exists: #421
   URL: https://github.com/org/repo/pull/421
   State: MERGED

ℹ️  PR is already merged. Merge log should be in main.
   View with: gh pr view https://github.com/org/repo/pull/421
```

### PR Not Merged Yet

```bash
$ ./scripts/create_verified_merge_log_pr.sh 425

🔍 Preflight checks...
✅ All dependencies available

🔍 Checking PR #425 state...
❌ PR #425 is not merged yet (state: OPEN)
   URL: https://github.com/org/repo/pull/425
   Wait for merge, then re-run this script.
```

## Requirements

- **git** - Repository must be a git repo
- **gh** - GitHub CLI (`gh`) must be installed and authenticated
- **python3** - With `json`, `subprocess`, `pathlib` modules (stdlib)
- **bash** - Shell script runner

## Integration

### Post-Merge Workflow

```bash
# 1. Feature PR is merged (e.g., PR #430)
# 2. Create merge log PR
./scripts/create_verified_merge_log_pr.sh 430

# 3. Enable auto-merge (optional)
gh pr merge --auto --squash --delete-branch

# 4. Done! Merge log will be in main after PR approval
```

### Automation (Optional)

You can integrate this into CI/CD:

```yaml
# .github/workflows/merge-log.yml
name: Create Merge Log PR
on:
  pull_request:
    types: [closed]

jobs:
  merge-log:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Create Merge Log PR
        run: |
          ./scripts/create_verified_merge_log_pr.sh ${{ github.event.pull_request.number }}
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Troubleshooting

### "Branch exists and has conflicts"

The script uses `--force-with-lease` when pushing. If you manually edited the remote branch, you might need to:

```bash
# Delete remote branch manually
git push origin --delete docs/merge-log-pr-<NUM>

# Re-run script
./scripts/create_verified_merge_log_pr.sh <NUM>
```

### "No changes to commit"

This means the merge log already exists in your local branch. This is expected behavior when:
- Running twice locally without pushing
- The file was already committed manually

Simply run `git checkout main` to reset.

### "PR not found"

Make sure:
- PR number is correct
- You have access to the repository
- `gh` is authenticated: `gh auth status`

## Development

### Testing Idempotency

```bash
# Run twice - second run should detect existing PR
./scripts/create_verified_merge_log_pr.sh 418
./scripts/create_verified_merge_log_pr.sh 418  # Should exit gracefully
```

### Dry Run (Local Only)

```bash
# Stop before pushing
./scripts/create_verified_merge_log_pr.sh 420
# Review changes
git diff
git log -1
# Abort
git reset --hard origin/main
git checkout main
git branch -D docs/merge-log-pr-420
```

## See Also

- `docs/ops/README.md` - Index of all verified merge logs
- `docs/ops/PR_*_MERGE_LOG.md` - Individual merge log documents

---

**Script Location:** `scripts/create_verified_merge_log_pr.sh`  
**Last Updated:** 2025-12-28  
**Maintainer:** Operations Team
