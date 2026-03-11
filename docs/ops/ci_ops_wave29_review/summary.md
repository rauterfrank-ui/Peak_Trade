# Wave 29 — Required Contexts Proof Review — Summary

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave29-required-contexts-proof-review  
**Mode:** Proof-only; zero functional mutation

---

## Executive Summary

Wave 29 gathered exact proof around required checks and contexts. **Key finding:** The repo config and docs state that only "PR Gate" is required for branch protection. The actual GitHub branch protection API shows **9 required contexts**, and **PR Gate is not among them**. Config `ignored_contexts` lists several checks that are actually required by GitHub. This docs/config-to-reality gap is documented; no changes were made.

---

## Workflow / Check Counts

- **PR-critical workflows inventoried:** 11
- **Check names from workflows:** 16+
- **Branch protection required (GitHub API):** 9
- **Config required (required_status_checks.json):** 1 (PR Gate)

---

## Live Context Summary

| Source | Required Contexts |
|--------|-------------------|
| GitHub Branch Protection | Guard tracked files, audit, tests (3.11), strategy-smoke, Policy Critic Gate, Lint Gate, dispatch-guard, docs-token-policy-gate, docs-reference-targets-gate |
| Config | PR Gate only |
| PR Gate in branch protection? | **No** |

---

## Docs-Reality Gaps

1. CI.md and GATES_OVERVIEW claim "only PR Gate required" — contradicted by GitHub API.
2. Config `ignored_contexts` includes checks that are required by GitHub.
3. Config notes say "Branch protection requires only PR Gate" — inaccurate for current GitHub state.
4. Unclear whether config describes target state or outdated snapshot.

---

## Classification Summary

- **DOCS_CLARIFICATION_SAFE:** 2 items (add config-vs-GitHub clarification)
- **NEEDS_PROOF_BEFORE_CHANGE:** 6+ items (config alignment, branch protection, dispatch guard doc)
- **DO_NOT_TOUCH:** config, workflows, scripts, untracked docs

---

## First Safe Follow-Up

Docs-only: Add one sentence to CI.md and GATES_OVERVIEW clarifying that config describes repo contract and GitHub branch protection may differ. No config/workflow/branch protection changes.

---

## Validation

- All required output files created
- No workflow/script/config changes
- Untracked docs preserved (not staged)
