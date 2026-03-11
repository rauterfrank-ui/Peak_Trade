# Wave 26 CI/Ops Inventory — Counts

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave26-ci-ops-hygiene-review

---

## By Area

| Area | Count | Notes |
|------|-------|------|
| ci | 58 | Workflows, scripts, config, docs |
| ops | 24 | Runbooks, indexes, ops docs |
| docs | 2 | INDEX.md, root indexes |
| audit | 4 | Audit reports, indexes |
| root | 2 | Pre-flight, workflow overview |

---

## By Kind

| Kind | Count | Notes |
|------|-------|------|
| workflow | 35 | .github&#47;workflows&#47;*.yml |
| script | 16 | scripts&#47;ci&#47;*, scripts&#47;ops&#47;* |
| doc | 28 | docs&#47;ops&#47;*, docs&#47;audit&#47;* |
| runbook | 12 | docs&#47;ops&#47;runbooks&#47;* |
| index | 5 | INDEX, RUNBOOK_INDEX, audit README |
| config | 1 | required_status_checks.json |
| audit_report | 2 | GOVERNANCE_DATAFLOW, REPO_AUDIT |
| untracked_local | 2 | docs/GOVERNANCE_DATAFLOW, docs/REPO_AUDIT |

---

## By Initial Bucket

| Bucket | Count |
|--------|-------|
| KEEP_AS_IS | 78 |
| DOCS_ALIGNMENT_CANDIDATE | 4 |
| WORKFLOW_HYGIENE_CANDIDATE | 1 |

---

## Operational Risk Summary

| Risk Level | Count |
|------------|-------|
| CRITICAL | 8 |
| HIGH | 18 |
| MEDIUM | 35 |
| LOW | 21 |

---

## Full Workflow Count (Reference)

Total workflows in `.github&#47;workflows&#47;`: **67** (inventory samples 35 most relevant for CI/Ops)
