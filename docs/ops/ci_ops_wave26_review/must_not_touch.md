# Wave 26 — Must NOT Touch

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave26-ci-ops-hygiene-review

---

## Explicit Preservation (Hard Guardrails)

| Path | Reason |
|------|--------|
| docs&#47;GOVERNANCE_DATAFLOW_REPORT.md | Untracked; explicit Wave 25/26 preservation; do not add, modify, delete, or stage |
| docs&#47;REPO_AUDIT_REPORT.md | Untracked; explicit Wave 25/26 preservation; do not add, modify, delete, or stage |

---

## Critical — No Changes Without Proof

| Path / Area | Reason |
|-------------|--------|
| .github&#47;workflows&#47;ci.yml | Primary CI; PR Gate; tests; strategy-smoke; CRITICAL |
| config&#47;ci&#47;required_status_checks.json | Branch protection contract; required contexts |
| .github&#47;workflows&#47;required-checks-hygiene-gate.yml | Required checks drift validation |
| .github&#47;workflows&#47;ci-workflow-dispatch-guard.yml | Workflow dispatch guard |
| .github&#47;workflows&#47;lint_gate.yml | Lint Gate |
| .github&#47;workflows&#47;policy_critic_gate.yml | Policy Critic Gate |
| .github&#47;workflows&#47;docs-token-policy-gate.yml | Docs token policy |
| .github&#47;workflows&#47;docs_reference_targets_gate.yml | Docs reference targets |
| .github&#47;workflows&#47;docs_diff_guard_policy_gate.yml | Docs diff guard |
| .github&#47;workflows&#47;policy_tracked_reports_guard.yml | Guard tracked reports |
| docs&#47;ops&#47;GATES_OVERVIEW.md | Canonical SSoT for gates |
| docs&#47;INDEX.md | Canonical documentation index |
| docs&#47;ops&#47;RUNBOOK_INDEX.md | Canonical runbook navigation |
| docs&#47;audit&#47;README.md | Canonical audit navigation |
| docs&#47;audit&#47;AUDIT_RUNBOOK_COMPLETE.md | Operational audit runbook |
| docs&#47;ops&#47;runbooks&#47; | Operational runbooks |
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
