# Wave 29 — Classification

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave29-required-contexts-proof-review

---

## Classification Buckets

| Bucket | Definition | Wave 29 Scope |
|--------|------------|---------------|
| **DOCS_CLARIFICATION_SAFE** | Docs-only changes that clarify without changing config/workflow/branch protection | Add clarifying notes about config vs GitHub |
| **NEEDS_PROOF_BEFORE_CHANGE** | Any change to config, branch protection, workflow names, or required-check semantics | Config alignment; branch protection changes |
| **DO_NOT_TOUCH** | Paths/areas that must not be modified in any follow-up without explicit operator decision | config, workflows, scripts |

---

## Findings by Bucket

### DOCS_CLARIFICATION_SAFE

| ID | Item | Rationale |
|----|------|-----------|
| A05 | Clarify config vs GitHub scope in docs | Add one sentence: config describes repo contract; GitHub branch protection is managed separately |
| F11 (Wave 26) | Required vs ignored contexts explanation | Add to GATES_OVERVIEW or CI.md: "Config required_contexts/ignored_contexts are repo contract; actual GitHub branch protection may differ." |

### NEEDS_PROOF_BEFORE_CHANGE

| ID | Item | Rationale |
|----|------|-----------|
| A01 | Config vs GitHub alignment | Changing required_status_checks.json to match GitHub would alter repo contract; requires operator decision |
| A02, A03 | Docs branch protection claims | Updating to "9 checks required" would document current state; but if target is "PR Gate only", docs change could mislead |
| A04 | ignored_contexts vs GitHub required | Aligning config with GitHub is a config change; high risk |
| A06 | WORKFLOW_DISPATCH_GUARD doc | Updating "Required Check Active" would change operator expectations; verify intent first |
| F01, F04, F05, F06 (Wave 26) | Audit paths, check names, dispatch guard | Per Wave 26 classification |

### DO_NOT_TOUCH

| Path / Area | Reason |
|-------------|--------|
| config/ci/required_status_checks.json | Branch protection contract; no change without proof |
| .github/workflows/*.yml | Workflow semantics; no change in proof wave |
| docs/GOVERNANCE_DATAFLOW_REPORT.md | Untracked; explicit preservation |
| docs/REPO_AUDIT_REPORT.md | Untracked; explicit preservation |
| scripts/ci/validate_required_checks_hygiene.py | Validates config; no change |
| GitHub branch protection settings | Operator-controlled; no automated change |

---

## Summary Counts

- **DOCS_CLARIFICATION_SAFE:** 2 items
- **NEEDS_PROOF_BEFORE_CHANGE:** 6+ items
- **DO_NOT_TOUCH:** 6+ paths/areas
