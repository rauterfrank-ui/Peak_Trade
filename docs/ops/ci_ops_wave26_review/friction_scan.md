# Wave 26 CI/Ops Hygiene — Friction Scan

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave26-ci-ops-hygiene-review  
**Mode:** Review-only; evidence-based

---

## Summary

High-signal hygiene friction points identified from current repo state. No speculative breakage claims. Evidence from paths/content only.

---

## 1. Duplicate / Overlapping Documentation

### 1.1 Audit Report Path Ambiguity
- **Evidence:** `docs&#47;INDEX.md` links to `audit&#47;GOVERNANCE_DATAFLOW_REPORT.md` and `audit&#47;REPO_AUDIT_REPORT.md` (Historical).
- **Friction:** Untracked `docs&#47;GOVERNANCE_DATAFLOW_REPORT.md` and `docs&#47;REPO_AUDIT_REPORT.md` exist at repo root of docs/. Wave 25 explicitly preserves both; relationship (duplicate? different version? migration artifact?) not documented for operators. <!-- pt:ref-target-ignore -->
- **Impact:** Operator confusion; unclear which to use for reference.

### 1.2 CI Pragmatic Flow Docs Overlap
- **Evidence:** `docs&#47;ops&#47;ci_pragmatic_flow_inventory.md`, `ci_pragmatic_flow_meta_gate.md`, `ci_pragmatic_flow_pr_body.md` exist alongside `docs&#47;ops&#47;CI.md` and `docs&#47;ops&#47;GATES_OVERVIEW.md`.
- **Friction:** Multiple docs describe CI flow; potential overlap with GATES_OVERVIEW (canonical SSoT for gates).
- **Impact:** Maintenance burden; risk of drift between docs.

### 1.3 Status Docs
- **Evidence:** `docs&#47;ops&#47;STATUS_MATRIX.md`, `docs&#47;ops&#47;STATUS_OVERVIEW_2026-02-19.md`.
- **Friction:** Two status-oriented docs; scope/purpose difference not clearly documented.
- **Impact:** Unclear which is authoritative for current status.

---

## 2. Naming / Convention Mismatches

### 2.1 Check Name Conventions
- **Evidence:** `config&#47;ci&#47;required_status_checks.json` uses `"PR Gate"`; `ignored_contexts` lists `"docs-reference-targets-gate"`, `"Lint Gate"`, `"Policy Critic Gate"`, etc. GATES_OVERVIEW uses mixed formats (Gate ID vs Display Name).
- **Friction:** Inconsistent naming between config, workflow job names, and docs.
- **Impact:** Harder to map config to workflows when troubleshooting.

### 2.2 Workflow File Naming
- **Evidence:** Mix of `ci-workflow-dispatch-guard.yml` (hyphen) and `required-checks-hygiene-gate.yml` (hyphen). Most use hyphens; a few use underscores (e.g. `merge_log_hygiene.yml`).
- **Friction:** Minor inconsistency in workflow file naming.
- **Impact:** Low; cosmetic.

---

## 3. Unclear / Stale References

### 3.1 Workflow Dispatch Guard Status
- **Evidence:** `docs&#47;ops&#47;ci&#47;WORKFLOW_DISPATCH_GUARD_GITHUB_SETTINGS.md` states "Required Check Active: ❌ No (not present in main required checks list)".
- **Friction:** `config&#47;ci&#47;required_status_checks.json` has `"dispatch-guard"` in `ignored_contexts`. Unclear if doc is describing intentional state or outdated.
- **Impact:** Operator may try to add dispatch-guard to required checks when it is intentionally excluded.

### 3.2 INSTALLATION_UND_ROADMAP Link
- **Evidence:** `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md` links to `INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md` at repo root.
- **Friction:** Need to verify file exists and is current.
- **Impact:** Broken link would reduce discoverability.

### 3.3 docs/runbooks/ vs docs/ops/runbooks/
- **Evidence:** `docs&#47;INDEX.md` lists `runbooks&#47;` under Operational. `docs&#47;ops&#47;RUNBOOK_INDEX.md` points to `runbooks&#47;` (relative) and `..&#47;..&#47;PRE_FLIGHT_CHECKLIST_RUNBOOK_OPS.md` (from docs&#47;ops&#47;). <!-- pt:ref-target-ignore -->
- **Friction:** INDEX "runbooks/" could resolve to `docs&#47;runbooks&#47;` or `docs&#47;ops&#47;runbooks&#47;`; structure suggests `docs/ops/runbooks/` is canonical.
- **Impact:** Possible broken or ambiguous link from INDEX.

---

## 4. Runbook Discoverability

### 4.1 docs/ops/workflows/ Not in Runbook README
- **Evidence:** `docs&#47;ops&#47;workflows&#47;` contains `WORKFLOW_NOTES_FRONTDOOR.md`, `PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md`. `docs&#47;ops&#47;runbooks&#47;README.md` does not list these. `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md` does.
- **Friction:** Workflow policy docs live in workflows/; runbook index focuses on runbooks/. Discoverability depends on WORKFLOW_RUNBOOK_OVERVIEW.
- **Impact:** Operators may miss workflow policy docs if they only use RUNBOOK_INDEX.

### 4.2 Ops Scripts → Runbook Mapping
- **Evidence:** 270+ scripts in `scripts&#47;ops&#47;`. `docs&#47;ops&#47;WORKFLOW_SCRIPTS.md`, `OPS_SCRIPT_TEMPLATE_GUIDE.md` exist but no single script-to-runbook index.
- **Friction:** Many scripts; unclear which runbook documents which script.
- **Impact:** Harder to find operational procedure for a given script.

---

## 5. Required Checks / Branch Protection Clarity

### 5.1 Required vs Ignored Contexts
- **Evidence:** `required_status_checks.json` requires only "PR Gate"; many gates in `ignored_contexts`. GATES_OVERVIEW documents all gates.
- **Friction:** Docs do not explicitly state "only PR Gate is required; other gates are informational or ignored for branch protection."
- **Impact:** Operators may expect all documented gates to be required.

### 5.2 required-checks-hygiene-gate Purpose
- **Evidence:** Workflow validates that required checks are hygiene-compliant (no path-filtered-only checks).
- **Friction:** Purpose is clear in GATES_OVERVIEW but not surfaced in a single "CI required checks explained" doc.
- **Impact:** Low; GATES_OVERVIEW covers it.

---

## 6. Scheduled Workflow Variable Gates

### 6.1 Variable Gates Documentation
- **Evidence:** `docs&#47;ops&#47;CI_SCHEDULED_WORKFLOW_VARIABLE_GATES.md` is canonical. CI.md references it.
- **Friction:** None significant; cross-reference is correct.
- **Impact:** None.

---

## 7. Evidence Chain / Merge Logs

### 7.1 Merge Log Location
- **Evidence:** Merge logs in `docs&#47;ops&#47;merge_logs&#47;` and `docs&#47;ops&#47;PR_*_MERGE_LOG.md` (root of ops). INDEX lists both.
- **Friction:** Two locations; convention (when to use which) may be unclear.
- **Impact:** Low; both are documented.

---

## Excluded (No Friction or Out of Scope)

- Workflow semantics (no change in this wave)
- Runtime/dataflow (explicitly out of scope)
- Evidence generation logic (no doc friction identified)
- Service/process supervision (no doc friction identified)
