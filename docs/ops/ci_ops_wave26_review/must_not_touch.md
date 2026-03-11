# Wave 26 — Must NOT Touch

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave26-ci-ops-hygiene-review

---

## Explicit Preservation (Hard Guardrails)

| Path | Reason |
|------|--------|
| docs/GOVERNANCE_DATAFLOW_REPORT.md | Untracked; explicit Wave 25/26 preservation; do not add, modify, delete, or stage |
| docs/REPO_AUDIT_REPORT.md | Untracked; explicit Wave 25/26 preservation; do not add, modify, delete, or stage |

---

## Critical — No Changes Without Proof

| Path / Area | Reason |
|-------------|--------|
| .github/workflows/ci.yml | Primary CI; PR Gate; tests; strategy-smoke; CRITICAL |
| config/ci/required_status_checks.json | Branch protection contract; required contexts |
| .github/workflows/required-checks-hygiene-gate.yml | Required checks drift validation |
| .github/workflows/ci-workflow-dispatch-guard.yml | Workflow dispatch guard |
| .github/workflows/lint_gate.yml | Lint Gate |
| .github/workflows/policy_critic_gate.yml | Policy Critic Gate |
| .github/workflows/docs-token-policy-gate.yml | Docs token policy |
| .github/workflows/docs_reference_targets_gate.yml | Docs reference targets |
| .github/workflows/docs_diff_guard_policy_gate.yml | Docs diff guard |
| .github/workflows/policy_tracked_reports_guard.yml | Guard tracked reports |
| docs/ops/GATES_OVERVIEW.md | Canonical SSoT for gates |
| docs/INDEX.md | Canonical documentation index |
| docs/ops/RUNBOOK_INDEX.md | Canonical runbook navigation |
| docs/audit/README.md | Canonical audit navigation |
| docs/audit/AUDIT_RUNBOOK_COMPLETE.md | Operational audit runbook |
| docs/ops/runbooks/ | Operational runbooks |
| PRE_FLIGHT_CHECKLIST_RUNBOOK_OPS.md | Pre-flight runbook |
| WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md | Workflow overview |

---

## Friction Items Classified as NEEDS_PROOF_BEFORE_CHANGE

| ID | Item | Reason |
|----|------|--------|
| F01 | Audit report path ambiguity | Untracked docs preservation; evidence chain |
| F04 | Check name conventions | Config affects branch protection |
| F05 | Workflow file naming | Rename could break triggers |
| F06 | Dispatch guard status doc | Could affect operator branch protection config |

---

## Summary

- **2** paths: explicit untracked preservation
- **18** paths: critical operational; no change without proof
- **4** friction items: NEEDS_PROOF_BEFORE_CHANGE
