# Wave 29 — First Safe Follow-Up (Docs-Only)

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave29-required-contexts-proof-review

---

## Scope

The **first possible future safe docs-only clarification wave** that:
- Does **not** change workflow YAML, config, scripts, or branch protection
- Does **not** add, modify, delete, or stage `docs&#47;GOVERNANCE_DATAFLOW_REPORT.md` or `docs&#47;REPO_AUDIT_REPORT.md`
- Only adds clarifying text to existing tracked docs

---

## Proposed Docs-Only Changes

### 1. CI.md

**Location:** After "Branch Protection:" sentence (line ~8)

**Add:**
> Hinweis: `config/ci/required_status_checks.json` beschreibt den Repo-Vertrag (required_contexts/ignored_contexts). Die tatsächlichen GitHub Branch-Protection-Einstellungen werden separat verwaltet und können abweichen. Aktueller Stand: `gh api repos/<owner>/<repo>/branches/main/protection`.

### 2. GATES_OVERVIEW.md

**Location:** In "Workflow → Jobs (Check-Namen) → Definition" Abschnitt, nach "Branch Protection: Nur **PR Gate** ist required"

**Add:**
> Die tatsächlichen required contexts auf GitHub können von der Config abweichen. Siehe `gh api repos/<owner>/<repo>/branches/main/protection` für den aktuellen Stand.

---

## Excluded from First Safe Follow-Up

- Any change to `required_status_checks.json`
- Any change to workflow files
- Any change to branch protection (operator-only)
- Any change to `docs/ops/ci/WORKFLOW_DISPATCH_GUARD_GITHUB_SETTINGS.md` (NEEDS_PROOF_BEFORE_CHANGE)
- Untracked docs (GOVERNANCE_DATAFLOW_REPORT, REPO_AUDIT_REPORT)

---

## Prerequisites

- Operator review of proposed wording
- Confirmation that clarifying "config vs GitHub" does not conflict with intended operator workflow
