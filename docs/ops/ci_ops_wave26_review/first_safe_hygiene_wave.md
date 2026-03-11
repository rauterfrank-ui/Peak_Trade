# Wave 26 — First Safe Hygiene Wave Plan

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave26-ci-ops-hygiene-review

---

## Objective

Define the **smallest future hygiene wave** with the **lowest operational risk**. Preference: docs alignment first, then runbook discoverability, workflow semantics only later and only with proof.

---

## Scope (Included)

### Tier 1: Docs Alignment (Lowest Risk)

| Action | Target | Validation |
|--------|--------|------------|
| F07: Verify link | `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md` → `INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md` | Link exists; fix if broken |
| F08: Clarify INDEX link | `docs&#47;INDEX.md` runbooks/ | Resolve to docs&#47;ops&#47;runbooks&#47; or correct path |
| F11: Add clarification | `docs&#47;ops&#47;GATES_OVERVIEW.md` or `docs&#47;ops&#47;CI.md` | One sentence: "Only PR Gate is required for branch protection; other gates are informational or in ignored_contexts." |
| F02: Align CI pragmatic flow docs | `ci_pragmatic_flow_*.md` vs GATES_OVERVIEW | Add cross-reference or consolidate; no deletion |
| F03: Clarify status docs | STATUS_MATRIX vs STATUS_OVERVIEW | Add one-line scope note to each |

### Tier 2: Runbook Discoverability (Low Risk)

| Action | Target | Validation |
|--------|--------|------------|
| F09: Add workflows to index | `docs&#47;ops&#47;runbooks&#47;README.md` or RUNBOOK_INDEX | Add "Workflow Policy Docs" section pointing to docs&#47;ops&#47;workflows&#47; |
| F10: Script index | `docs&#47;ops&#47;` | Add or extend script-to-runbook mapping; start with high-value scripts (CI, drift guard, merge logs) |

---

## Excluded (This Wave)

| ID | Item | Reason |
|----|------|--------|
| F01 | Audit report path ambiguity | NEEDS_PROOF; untracked docs preservation |
| F04 | Check name conventions | Config; branch protection risk |
| F05 | Workflow file naming | Rename risk; cosmetic |
| F06 | Dispatch guard status | Verify intent before doc change |
| All workflow YAML changes | — | Zero workflow changes |
| All script changes | — | Zero script changes |

---

## Safety Gates

1. **No workflow changes** — no edits to `.github&#47;workflows&#47;*.yml`
2. **No config changes** — no edits to `config&#47;ci&#47;required_status_checks.json`
3. **No script changes** — no edits to `scripts&#47;ci&#47;*`, `scripts&#47;ops&#47;*`
4. **docs&#47;GOVERNANCE_DATAFLOW_REPORT.md, docs&#47;REPO_AUDIT_REPORT.md** — untouched, unstaged
5. **Additive-only** — prefer adding clarifications over deleting content
6. **Link fixes only** — fix broken links; do not remove valid links

---

## Validation Required

- [ ] All links in modified docs verified (no broken links)
- [ ] docs-reference-targets-gate passes
- [ ] docs-token-policy-gate passes
- [ ] docs_diff_guard_policy_gate passes
- [ ] CI required checks unchanged
- [ ] No new required contexts added

---

## Expected Evidence Outputs

- `out&#47;ops&#47;ci_ops_wave26_review&#47;first_safe_hygiene_wave.md` (this file)
- Post-wave: PR with diff showing only docs changes; CI green

---

## Execution Order

1. F07: Verify INSTALLATION_UND_ROADMAP link
2. F08: Clarify INDEX runbooks link
3. F11: Add required vs ignored clarification to GATES_OVERVIEW or CI.md
4. F02: Cross-reference CI pragmatic flow docs
5. F03: Add scope notes to STATUS_MATRIX and STATUS_OVERVIEW
6. F09: Add workflows/ to runbook index
7. F10: Create or extend script index (minimal first pass)
