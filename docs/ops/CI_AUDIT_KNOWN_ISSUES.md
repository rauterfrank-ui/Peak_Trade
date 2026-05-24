# CI Audit — Known Issues

## Current status
- Historical context: GitHub [Issue #252](https://github.com/rauterfrank-ui/Peak_Trade/issues/252) tracked an older formatter drift described as a Black formatting/configuration issue.
- Current CI policy is Ruff-oriented. `scripts/ops/run_audit.sh` runs `ruff check .` and `ruff format --check .`; `scripts/ops/check_no_black_enforcement.sh` guards against `black --check` enforcement in workflows/scripts.
- `audit` findings are not all hard failures in every workflow path. In `.github/workflows/audit.yml`, `pip-audit` is blocking only for dependency-relevant changes and non-blocking for docs-only scope. The `run_audit.sh` step is currently wrapped so findings are surfaced but do not by themselves fail that workflow step.
- `lint_gate.yml` remains a separate enforcement surface: it always creates a check run, fails on Black-enforcement drift, and runs Ruff lint/format checks when Python files changed.

## What to check
- Confirm `strategy-smoke`, `tests`, and health gates are green for merge readiness.
- If `audit` or lint/format checks report findings, cross-check the workflow, trigger, and changed-file scope before treating the finding as merge-blocking.
- Distinguish technically enforced gates from advisory audit output or policy-language documentation.

## Tracking
- Historical formatter drift / Black wording: [Issue #252](https://github.com/rauterfrank-ui/Peak_Trade/issues/252)
- Current formatter source of truth: Ruff format checks, not Black enforcement.

## Local reproduction
```bash
ruff check .
ruff format --check .
bash scripts/ops/check_no_black_enforcement.sh
```

## Blocking model
- Technically enforced:
  - `pip-audit` in `.github/workflows/audit.yml` when dependency-relevant files changed.
  - `lint_gate.yml` Ruff lint/format checks when Python files changed.
  - `lint_gate.yml` Black-enforcement drift guard.
- Advisory / surfaced but not hard-failing in the current `audit.yml` wrapper:
  - `run_audit.sh` findings emitted by the `Run audit script (full checks)` step.
  - `pip-audit` findings for docs-only scope.
- Policy-language only:
  - Any historical reference to Black or Issue #252 unless a workflow/script actually enforces Black.

## Next steps
1. Clarify policy/docs if CI enforcement changes.
2. Keep future wording aligned with Ruff format/check surfaces and workflow-specific blocking behavior.
3. Do not perform a broad Black formatting sweep from this historical issue alone.
## Cybersecurity owner-triage notes for retained CI/Ops risks v0

This note records the post-HOLD owner-triage outcome for retained cybersecurity findings R-001 through R-007. It is a documentation-only boundary note for CI/Ops known issues. It does not authorize implementation, workflow dispatches, runtime execution, scheduler or daemon control, testnet/live activity, broker/exchange/order activity, or any change to Master V2 / Double Play trading semantics.

### Source artifacts

- Owner-triage report: `/tmp/peak_trade_cybersecurity_post_hold_owner_triage_20260510T150908Z/CYBERSECURITY_POST_HOLD_OWNER_TRIAGE.md`
- Full lossless retained candidate inventory: `/tmp/peak_trade_full_lossless_risk_inventory_readonly_20260508T163523Z/FULL_LOSSLESS_RISK_CANDIDATES.jsonl`
- Top review queue: `/tmp/peak_trade_full_lossless_risk_clusters_readonly_20260508T163641Z/TOP_REVIEW_QUEUE.jsonl`
- Repo-static successor inventory (durable archive; **not** lossless-equivalent; does **not** restore missing 20260508 JSONL; does **not** claim R-001/R-002/R-007 mapping): `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/inventory/repo_static_cybersecurity_risk_candidates/repo_static_cybersecurity_risk_candidates_jsonl_generation_v0_20260524T070050Z/REPO_STATIC_CYBERSECURITY_RISK_CANDIDATES.jsonl` — manifest verified (`MANIFEST_VERIFY_RC=0`); candidate rows: `162`; generation token: `repo_static_cybersecurity_risk_candidates_jsonl_generation_v0`

### Owner-triage outcome

The retained confirmed-risk candidates R-001 through R-007 remain accepted as cybersecurity follow-up items. They are retained for controlled follow-up, not discarded or downgraded by this note.

### Boundary

Allowed follow-up classes start with documentation-only or offline deterministic tests-only work that reuses existing CI/Ops/security surfaces.

This note explicitly does not authorize:

- scheduler, daemon, paper/shadow/testnet/live, broker, exchange, or order-submission execution
- workflow dispatches or CI-triggering changes as a side effect of triage
- runtime or hot-path changes
- Master V2 / Double Play logic changes
- Scope/Capital, Risk/KillSwitch, Execution/Live Gate, dashboard authority, AI authority, or strategy live-authority changes
- new parallel Evidence, Readiness, Map, Registry, Handoff, Package, or Pointer surfaces

### No-regression constraints

Any later mitigation for R-001 through R-007 must preserve:

- system capability
- trading logic
- Master V2 / Double Play semantics
- hot-path performance
- existing fail-closed safety posture
- traceability to the retained lossless inventory

### Recommended first slice from owner-triage

```text
Docs-only clarification in `docs/ops/CI_AUDIT_KNOWN_ISSUES.md`, adding a retained cybersecurity post-HOLD owner-triage note for R-001 through R-007. No workflow, script, runtime, testnet/live, broker/exchange/order, trading logic, Master V2, or Double Play changes.
```

### Proposed branch name (reference)

```text
`docs/cyber-post-hold-owner-triage-known-issues`
```

### Proposed files in scope (reference)

```text
- `docs/ops/CI_AUDIT_KNOWN_ISSUES.md`
```

### Proposed files out of scope (reference)

```text
- `.github/workflows/**`
- `scripts/ops/**`
- `src/**`
- `tests/**`
- `out/**`
- `reports/**`
- `docs/ops/registry/DOCS_TRUTH_MAP.md` unless an existing drift rule requires it
```

### Proposed validation commands (reference)

```text
Not executed in this turn:

- `git diff --check`
- `python3 scripts/ops/check_docs_drift_guard.py --base origin/main`
- No pytest for the docs-only first slice unless requested later.
```

### Stop conditions (reference)

```text
Stop if any action would run scheduler/daemon/paper/shadow/testnet/live commands, dispatch workflows, mutate evidence, access secrets, touch broker/exchange/order paths, alter risk/killswitch/execution semantics, or change trading/Master V2/Double Play behavior.
```

### Final verdict (reference)

```text
Proceed first with the docs-only known-issues clarification. It preserves every confirmed finding, maximizes no-regression safety, reuses an existing surface, and avoids runtime/hot-path changes.

RESULT=/tmp/peak_trade_cybersecurity_post_hold_owner_triage_20260510T150908Z/CYBERSECURITY_POST_HOLD_OWNER_TRIAGE.md
FIRST_SLICE=docs-only clarification in docs/ops/CI_AUDIT_KNOWN_ISSUES.md for retained R-001 through R-007 owner-triage boundaries
BRANCH=docs/cyber-post-hold-owner-triage-known-issues
IMPLEMENT_NOW=false
NO_LOGIC_CHANGE=true
NO_PERFORMANCE_REGRESSION=true
```

## Cybersecurity Visibility Chain — canonical owner inventory v0

**Anchor for this chain:** this file (`docs/ops/CI_AUDIT_KNOWN_ISSUES.md`). Registry pointers: [`docs/ops/registry/DOCS_TRUTH_MAP.md`](registry/DOCS_TRUTH_MAP.md) (Änderungsnachweis). **Non-authorizing:** static visibility contracts and this inventory do **not** authorize runtime, scheduler/daemon, paper/shadow/testnet/live, broker/exchange, or order-submission behavior.

### Retained cybersecurity risks R-001 through R-007

| ID | Repo-mapped static owner | Status |
|----|--------------------------|--------|
| R-001 | — | **Pending** — no repo test owner; requires lossless inventory recovery |
| R-002 | — | **Pending** — no repo test owner; requires lossless inventory recovery |
| R-003 | `tests/ops/test_run_sample_size_ramp_script_contract_v0.py` | mapped |
| R-004 | `tests/ops/test_run_testnet_evidence_flow_v2_script_contract_v0.py` | mapped |
| R-005 | `tests/ops/test_knowledge_prod_smoke_script.py` | mapped |
| R-006 | `tests/ci/test_prcd_aws_export_write_smoke_workflow_contract_v0.py` | mapped |
| R-007 | — | **Pending** — no repo test owner; requires lossless inventory recovery |

> R-001/R-002/R-007 IDs here are the **post-HOLD lossless-inventory** set (see Source artifacts above), not `docs/ops/RISK_REGISTER.md` ops-register IDs.

### Static visibility contract owners (reuse — do not duplicate)

| Surface | Owner module |
|---------|--------------|
| Workflow secrets/vars/braced contexts (hub) | `tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py` |
| Workflow write permissions | `tests/ci/test_workflow_write_permissions_visibility_contract_v0.py` |
| Workflow network/gh markers | `tests/ci/test_workflow_network_gh_marker_visibility_contract_v0.py` |
| Manual-dispatch sensitive surfaces | `tests/ci/test_workflow_manual_dispatch_sensitive_surface_contract_v0.py` |
| Workflow artifact retention | `tests/ci/test_workflow_artifact_retention_visibility_contract_v0.py` |
| Workflow permission boundary | `tests/ops/test_workflow_permission_boundary_visibility_v1.py` |
| WebUI API security-header routes | `tests/webui/test_webui_api_security_headers_visibility_contract_v0.py` |
| No `pull_request_target` + checkout v5 pin | `tests/ci/test_workflows_no_pull_request_target_contract_v0.py` |
