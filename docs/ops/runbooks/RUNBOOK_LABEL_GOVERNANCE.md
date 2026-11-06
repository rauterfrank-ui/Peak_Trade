# RUNBOOK — GitHub Labels Governance (Peak_Trade)

Status: ACTIVE  
Scope: repo-wide labels (pull requests + repo metadata)  
Note: **Issues are disabled** in rauterfrank-ui/Peak_Trade.

Default mode: audit and decision are docs-only (no label changes without Operator approval)

---

## Purpose

Deterministic, governance-safe process for:
- Audit artifacts (snapshot, refs scans, usage counts, operational refs per label)
- Decision (KEEP / DEPRECATE / MIGRATE / DELETE) without changes
- Operator-only migration (rename or relabel) and Operator-only delete
- Verification and rollback
- Always update documentation after any change

---

## Stop Rules (Hard)

STOP if:
- Operator-only steps are executed without explicit approval
- tmp labels json snapshot is missing
- operational hard-refs in .github or scripts exist for a label being changed
- rollback plan is missing (migration or delete)
- API errors lead to non-deterministic outcomes

---

## Phase 0 — Pre-Flight (Snapshot-only)

```bash
set -euo pipefail
echo "If your prompt shows '>' or 'dquote>' or heredoc continuation: press Ctrl-C once."
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$(pwd)"
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status -sb 2>/dev/null || true
gh auth status 2>/dev/null || true
gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true
```
