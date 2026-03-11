# Wave 29 — Docs-to-Reality Mapping

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave29-required-contexts-proof-review

---

## 1. CI.md

| Statement | Reality | Status |
|-----------|---------|--------|
| "Nur **PR Gate** ist als required check konfiguriert" | Config (`required_status_checks.json`) has `required_contexts: ["PR Gate"]` | **Accurate for config** |
| "Alle anderen Gates ... sind informational bzw. in `ignored_contexts`" | Config has many in `ignored_contexts` | **Accurate for config** |
| Implied: Branch protection requires only PR Gate | **GitHub branch protection requires 9 checks; PR Gate not among them** | **Inaccurate for GitHub reality** |

---

## 2. GATES_OVERVIEW.md

| Statement | Reality | Status |
|-----------|---------|--------|
| "Branch Protection: Nur **PR Gate** ist required" | GitHub branch protection has 9 required; PR Gate not in list | **Inaccurate for GitHub reality** |
| "alle anderen dokumentierten Gates sind informational oder in `ignored_contexts`" | Config matches; but branch protection requires several of these | **Ambiguous** |
| Workflow → Job mapping table | Matches workflow YAML job names | **Accurate** |
| Always-run vs path-filtered classification | Matches workflow triggers | **Accurate** |

---

## 3. config/ci/required_status_checks.json

| Field | Value | Reality |
|-------|-------|---------|
| required_contexts | ["PR Gate"] | Config says PR Gate only |
| ignored_contexts | [tests (3.11), strategy-smoke, Lint Gate, Policy Critic Gate, ...] | Many of these are **actually required** by GitHub branch protection |
| notes | "Pragmatic flow: Branch protection requires only PR Gate" | **Contradicted by GitHub API** |

---

## 4. required-checks-hygiene-gate

- **Purpose:** Validates that config's `required_contexts` are produced by always-on workflows.
- **Config required:** PR Gate only.
- **Reality:** Branch protection uses different contexts; hygiene gate does not validate branch protection.

---

## 5. Summary of Gaps

1. **Config/docs claim:** Only PR Gate is required for branch protection.
2. **GitHub reality:** 9 checks are required; PR Gate is not one of them.
3. **Config `ignored_contexts`** lists checks that are **actually required** by branch protection (e.g. Lint Gate, Policy Critic Gate, dispatch-guard, docs-token-policy-gate, docs-reference-targets-gate, tests (3.11), strategy-smoke, Guard tracked files, audit).
4. **Uncertainty:** Whether config describes intended/target state vs. current GitHub settings. No evidence of when branch protection was last aligned with config.
