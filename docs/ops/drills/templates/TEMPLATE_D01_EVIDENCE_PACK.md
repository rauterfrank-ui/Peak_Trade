# D01 Evidence Pack — [DRILL_NAME]

**Date:** YYYY-MM-DD HH:MM  
**Operator:** [operator_id]  
**Drill ID:** [e.g., D03B, D04, etc.]  
**Session ID:** [optional: unique session identifier]

---

## Purpose

Capture baseline evidence **before** drill execution. Provides:
- Git state (SHA, branch, working tree)
- CI baseline (last successful run)
- Tool versions
- Environment details

**Not for:**
- Drill execution logs (use session template or drill-specific format)
- CI triage (use TEMPLATE_D02_CI_TRIAGE.md)

---

## Pre-Flight Check

### Terminal Setup

```bash
# Ensure no hanging processes
# Press Ctrl-C if needed to stop any running commands

# Navigate to repo root
cd /Users/frnkhrz/Peak_Trade || cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Verify location
pwd
# Expected: /Users/frnkhrz/Peak_Trade (or your repo path)

# Show git root
git rev-parse --show-toplevel
# Expected: same as pwd

# Git status (compact)
git status -sb
# Expected: clean working tree OR list of changes
```

**Output:**
```
[Paste terminal output here]
```

**Observation:**
- PWD: [path]
- Git root: [path]
- Branch: [branch name]
- Working tree: [clean / modified]

---

## Git State

### Current Branch & SHA

```bash
# Current branch
git branch --show-current

# Current SHA
git rev-parse HEAD

# Commits ahead/behind origin
git status -sb | head -1
```

**Output:**
```
[Paste terminal output here]
```

**Evidence:**
- **Branch:** [branch name]
- **SHA:** [commit hash]
- **Tracking:** [e.g., "origin/main", "ahead 2, behind 0"]

---

### Working Tree Status

```bash
# Show modified/staged/untracked files
git status --porcelain
```

**Output:**
```
[Paste terminal output here]
```

**Evidence:**
- **Modified files:** [count] (list if <5, otherwise note "see output above")
- **Staged files:** [count] (list if <5, otherwise note "see output above")
- **Untracked files:** [count] (list if <5, otherwise note "see output above")

**Assessment:** [CLEAN / MODIFIED]

---

### Recent Commits

```bash
# Last 5 commits on current branch
git log --oneline -5
```

**Output:**
```
[Paste terminal output here]
```

**Evidence:**
- **Most recent commit:** [SHA] — [message]
- **Context:** [e.g., "On main after D03A merge"]

---

## CI Baseline

### Last Successful Run (Main Branch)

```bash
# Query last successful run on main
gh run list --branch main --status success --limit 1 --json databaseId,displayTitle,conclusion,createdAt
```

**Output:**
```
[Paste terminal output here]
```

**Evidence:**
- **Run ID:** [database ID]
- **Workflow:** [display title]
- **Conclusion:** SUCCESS
- **Created:** [timestamp]
- **Link:** `https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/[RUN_ID]`

---

### Required Checks (from Branch Protection)

```bash
# List required checks (if available)
# Note: This may require API access or manual inspection
gh api repos/rauterfrank-ui/Peak_Trade/branches/main/protection | jq '.required_status_checks.contexts'
```

**Output:**
```
[Paste terminal output here OR note "Manual inspection required"]
```

**Evidence:**
- [Check 1]
- [Check 2]
- [Check 3]
- ...

**Source:** [API output / `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md` / manual inspection]

---

## Tool Versions

### GitHub CLI

```bash
gh --version
```

**Output:**
```
[Paste output here]
```

**Version:** [e.g., "gh version 2.60.1"]

---

### Python & UV

```bash
python3 --version
uv --version
```

**Output:**
```
[Paste output here]
```

**Versions:**
- **Python:** [e.g., "Python 3.11.5"]
- **UV:** [e.g., "uv 0.5.11"]

---

### Ruff (Linter)

```bash
uv run ruff --version
```

**Output:**
```
[Paste output here]
```

**Version:** [e.g., "ruff 0.8.4"]

---

### Git

```bash
git --version
```

**Output:**
```
[Paste output here]
```

**Version:** [e.g., "git version 2.47.0"]

---

## Environment

### Operating System

```bash
uname -a
```

**Output:**
```
[Paste output here]
```

**Evidence:**
- **OS:** [e.g., "Darwin 24.6.0 (macOS)"]
- **Architecture:** [e.g., "arm64"]

---

### Shell

```bash
echo $SHELL
$SHELL --version 2>/dev/null || echo "Version not available"
```

**Output:**
```
[Paste output here]
```

**Evidence:**
- **Shell:** [e.g., "/bin/zsh"]
- **Version:** [e.g., "zsh 5.9"]

---

### Current Directory Permissions

```bash
ls -ld .
```

**Output:**
```
[Paste output here]
```

**Evidence:**
- **Permissions:** [e.g., "drwxr-xr-x"]
- **Owner:** [e.g., "frnkhrz"]

---

## Documentation Baseline

### Docs Reference Targets (Baseline)

```bash
# Verify no broken links at baseline
./scripts/ops/verify_docs_reference_targets.sh
```

**Output:**
```
[Paste output here OR note "Check passed / X broken links found"]
```

**Evidence:**
- **Status:** [PASS / FAIL]
- **Broken links:** [count, if any]
- **Details:** [list if <5, otherwise note "see output above"]

---

### Lint Status (Baseline)

```bash
# Check for existing lint issues
uv run ruff check docs/ --exit-zero
```

**Output:**
```
[Paste output here OR note "No issues found"]
```

**Evidence:**
- **Status:** [CLEAN / ISSUES FOUND]
- **Issue count:** [count, if any]
- **Details:** [list if <5, otherwise note "see output above"]

---

## Evidence Summary

### Snapshot Checklist

- [ ] Git state captured (branch, SHA, working tree)
- [ ] CI baseline identified (last successful run)
- [ ] Tool versions documented (gh, uv, ruff, git)
- [ ] Environment documented (OS, shell, permissions)
- [ ] Docs baseline captured (link check, lint check)

### Key Observations

**Git Context:**
- **Branch:** [branch name]
- **SHA:** [commit hash]
- **Working Tree:** [CLEAN / MODIFIED]

**CI Context:**
- **Last Success:** Run [ID] on [date]
- **Required Checks:** [count] (see list above)

**Tool Context:**
- **gh:** [version]
- **Python:** [version]
- **UV:** [version]
- **Ruff:** [version]

**Environment Context:**
- **OS:** [OS name + version]
- **Shell:** [shell + version]

**Docs Context:**
- **Link Check:** [PASS / FAIL]
- **Lint Check:** [CLEAN / ISSUES]

---

## Risk Assessment (Pre-Drill)

**Risk Level:** [LOW / MED / HIGH]

**Rationale:**
- [Factor 1: e.g., "Clean working tree → no uncommitted changes"]
- [Factor 2: e.g., "CI baseline SUCCESS → repo stable"]
- [Factor 3: e.g., "Docs-only scope → low blast radius"]

**Blockers (if any):**
- [Blocker 1: e.g., "Working tree not clean → must commit/stash first"]
- [Blocker 2: e.g., "CI baseline FAILED → must fix before drill"]

**Recommendation:** [PROCEED / BLOCK / DEFER]

---

## References

**Drill Pack:**
- [DRILL_PACK_M01_D03A_STANDARD.md](../DRILL_PACK_M01_D03A_STANDARD.md)

**Operator Drill Pack:**
- [OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md](../OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md)

**Runbooks:**
- [RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md](../../runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md)

---

## Change Log

- **[Date]:** Evidence pack captured (operator: [name])
