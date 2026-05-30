# CI Audit — Known Issues

## Current status
- **PR #3726 / CI classifier (2026-05):** Contract/docs-only PRs that touched `tests&#47;webui&#47;test_market_dashboard_readonly_structure_contract_v0.py` still ran the full Python matrix because `tests&#47;webui&#47;**` matched the `code` path filter (`tests&#47;!(ci|ops)&#47;**`). **Policy fix (PR #3727):** whitelist `tests&#47;webui&#47;test_*_structure_contract*.py` in the `static_contract` bucket, exclude it from `code`, and run those files in Fast-Lane static-contract pytest alongside `tests&#47;ci` and `tests&#47;ops`. Mixed PRs with `src&#47;**` or other non-whitelisted test paths still set `code_changed=true` (fail closed).
- **PR #3728 validation (2026-05):** Fastpath validation PR proved #3727 YAML negation (`tests&#47;**` plus separate `!tests&#47;webui&#47;test_*_structure_contract*.py`) did **not** exclude WebUI structure-contract files at runtime — `dorny&#47;paths-filter` still set `code=true`, `run_matrix=true`, and Full Matrix ran. **Runtime fix (#3729):** replace broad `tests&#47;**` + `!` lines with picomatch extglob in the `code` bucket only: `tests&#47;!(ci|ops|webui)&#47;**`, `tests&#47;webui&#47;!(test_*_structure_contract*)&#47;**`, and `tests&#47;webui&#47;!(test_*_structure_contract*).py`. Root-level whitelisted structure-contract files match `static_contract` only; nested `tests&#47;webui&#47;subdir&#47;…` remains `code` (fail closed). `src&#47;**` and `templates&#47;**` unchanged.
- **PR #3730 revalidation (2026-05):** Post-#3729 structure-contract-only PR **runtime-confirmed** fastpath: `Filter code = false`, `static_contract = true`, `docs_or_static_contract_only = true`, `run_matrix = false`; `tests (3.9&#47;3.10&#47;3.11)` short-circuited with **Docs/static-contract PR — skip full matrix**; Fast-Lane ran `pytest tests&#47;ci tests&#47;ops` plus whitelisted `tests&#47;webui&#47;test_*structure_contract*.py` including `test_market_dashboard_readonly_structure_contract_v0.py`.
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
| R-001 | — | **Pending** — repo-static successor charter v0; no `candidate_id` assigned; definitive mapping requires lossless inventory row |
| R-002 | — | **Pending** — repo-static successor charter v0; no `candidate_id` assigned; definitive mapping requires lossless inventory row |
| R-003 | `tests/ops/test_run_sample_size_ramp_script_contract_v0.py` | mapped |
| R-004 | `tests/ops/test_run_testnet_evidence_flow_v2_script_contract_v0.py` | mapped |
| R-005 | `tests/ops/test_knowledge_prod_smoke_script.py` | mapped |
| R-006 | `tests/ci/test_prcd_aws_export_write_smoke_workflow_contract_v0.py` | mapped |
| R-007 | — | **Pending** — repo-static successor charter v0; no `candidate_id` assigned; definitive mapping requires lossless inventory row |

> R-001/R-002/R-007 IDs here are the **post-HOLD lossless-inventory** set (see Source artifacts above), not `docs/ops/RISK_REGISTER.md` ops-register IDs.

### Pending R-001/R-002/R-007 — repo-static successor inventory charter v0

```
CYBERSECURITY_VISIBILITY_R_PENDING_REPO_STATIC_INVENTORY_CHARTER_V0=true
LOSSLESS_JSONL_RECOVERY=false
REPO_STATIC_SUCCESSOR_INVENTORY=true
ORIGINAL_DURABLE_JSONL_REQUIRED_FOR_LOSSLESS_RECOVERY=true
FULL_LOSSLESS_RISK_CANDIDATES_JSONL_NOT_FOUND=true
REPO_STATIC_SUCCESSOR_DOES_NOT_CONTAIN_R001_R002_R007=true
REPO_STATIC_SUCCESSOR_DOES_NOT_CLAIM_LOSSLESS_EQUIVALENCE=true
R001_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false
R002_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false
R007_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false
CYBERSECURITY_VISIBILITY_R_PENDING_INVENTORY_CHARTER_DOCS_TESTS_ONLY=true
```

**Purpose:** Record interim visibility for retained risks **R-001**, **R-002**, and **R-007** while the missing 20260508 lossless inventory remains unavailable. This charter **does not** recover, regenerate, or claim equivalence to `FULL_LOSSLESS_RISK_CANDIDATES.jsonl` or `CYBERSECURITY_POST_HOLD_OWNER_TRIAGE.md`.

**Non-authorizing:** This section does not authorize workflow dispatches, runtime/scheduler/daemon/adapter execution, hooks, launchctl, Notion write/MCP/API, Market overlay enablement, S3/AWS/rclone, broker/exchange, Testnet/Live, or Master V2 / Double Play authority changes.

**Repo-static successor (interim review surface only):**

| Field | Value |
|-------|-------|
| Durable JSONL | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/inventory/repo_static_cybersecurity_risk_candidates/repo_static_cybersecurity_risk_candidates_jsonl_generation_v0_20260524T070050Z/REPO_STATIC_CYBERSECURITY_RISK_CANDIDATES.jsonl` |
| Generation token | `repo_static_cybersecurity_risk_candidates_jsonl_generation_v0` |
| Candidate rows | `162` |
| Manifest verify | `MANIFEST_VERIFY_RC=0` (per generation report in durable archive) |
| `inventory_kind` | `repo_static_successor_v0` (every row `lossless_equivalent=false`) |
| Retained-risk IDs in JSONL | **none** — successor extractor does **not** emit `R-001` / `R-002` / `R-007` |

**Interim classification histogram (repo-static; not R-ID mapping):**

| Classification | Row count | Notes |
|----------------|-----------|-------|
| `manual_dispatch_sensitive_surface` | 70 | Reuse `tests/ci/test_workflow_manual_dispatch_sensitive_surface_contract_v0.py` |
| `workflow_secrets_visibility` | 44 | Reuse `tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py` |
| `scheduler_or_runtime_boundary` | 24 | Reuse `tests/ops/test_scheduler_boundary_hard_block_contract_v0.py`; Reuse `tests/ops/test_p67_library_scheduler_boundary_opt_in_v0.py` |
| `branch_or_environment_authority` | 12 | Review-input only |
| `artifact_retention_or_evidence_gap` | 6 | Reuse `tests/ci/test_workflow_artifact_retention_visibility_contract_v0.py` |
| `paid_ai_eval_gate` | 4 | Review-input only |
| `docs_drift_or_pointer_integrity` | 2 | Review-input only |

```
CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_SCHEDULER_BOUNDARY_CROSSLINK_V0=true
CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_SCHEDULER_BOUNDARY_CROSSLINK_DOCS_TESTS_ONLY=true
INPUT_JSONL_PROVIDED=false
DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true
```

**Non-authorizing:** Explicit histogram reuse-owner crosslinks for `scheduler_or_runtime_boundary` are **visibility-only**; they do **not** authorize scheduler/daemon/runtime start, Testnet/Live, broker/exchange, or definitive R-001/R-002/R-007 mapping while `INPUT_JSONL_PROVIDED=false`.

Operators may use this histogram for **CI/Ops visibility triage** until a lossless row exists for each pending retained risk. **Do not** treat any `CSC-STATIC-v0-*` `candidate_id` as a substitute mapping for R-001/R-002/R-007 without restored lossless inventory or operator-approved triage.

**Lossless recovery still required for definitive R-001/R-002/R-007 mapping:**

| Artifact | Status |
|----------|--------|
| `/tmp/peak_trade_full_lossless_risk_inventory_readonly_20260508T163523Z/FULL_LOSSLESS_RISK_CANDIDATES.jsonl` | **Not found** at charter time |
| `/tmp/peak_trade_cybersecurity_post_hold_owner_triage_20260510T150908Z/CYBERSECURITY_POST_HOLD_OWNER_TRIAGE.md` | **Not found** at charter time |

**Approved recovery input (future slice only; not authorized here):** operator supplies durable `INPUT_JSONL=<absolute path>` to `FULL_LOSSLESS_RISK_CANDIDATES.jsonl` or equivalent approved triage artifact, then a separate read-only mapping slice may assign repo test owners — reusing this anchor and existing visibility contract modules only.

**Relationship to mapped risks R-003–R-006:** R-003 through R-006 retain their repo-mapped static test owners in the table above. This charter **does not** remap them.

### Pending R-001/R-002/R-007 — input artifact contract v0

```
CYBERSECURITY_VISIBILITY_R_PENDING_INPUT_ARTIFACT_CONTRACT_V0=true
LOSSLESS_JSONL_RECOVERY=false
DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true
INPUT_JSONL_REQUIRED=true
ACCEPTED_INPUT_ARTIFACTS=FULL_LOSSLESS_RISK_CANDIDATES.jsonl,APPROVED_OPERATOR_TRIAGE_ARTIFACT
NO_MAPPING_WITHOUT_INPUT_ARTIFACT=true
INPUT_JSONL_PROVIDED=false
R001_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false
R002_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false
R007_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false
CYBERSECURITY_VISIBILITY_R_PENDING_INPUT_ARTIFACT_CONTRACT_DOCS_TESTS_ONLY=true
```

**Purpose:** Normatively define which **operator-supplied durable artifacts** may authorize a **future separate** read-only mapping slice for definitive R-001/R-002/R-007 → repo test-owner assignment. This contract **does not** ingest files, **does not** assign `candidate_id` values, and **does not** set `LOSSLESS_JSONL_RECOVERY=true`.

**Non-authorizing:** No workflow dispatch, runtime/scheduler/daemon/adapter execution, hooks, launchctl, Notion write/MCP/API, Market overlay enablement, S3/AWS/rclone, broker/exchange, Testnet/Live, or Master V2 / Double Play authority changes.

**Accepted input artifacts (exactly one primary per mapping slice):**

| Token | Artifact | Requirements |
|-------|----------|--------------|
| `FULL_LOSSLESS_RISK_CANDIDATES.jsonl` | Post-HOLD lossless retained-risk candidate inventory | Operator provides durable absolute path via `INPUT_JSONL=<path>`; file must parse as JSONL; must contain rows identifiable as R-001/R-002/R-007 (or equivalent retained-risk IDs documented in triage); `MANIFEST.sha256` verify **RC=0** when a manifest is bundled with the durable copy |
| `APPROVED_OPERATOR_TRIAGE_ARTIFACT` | `CYBERSECURITY_POST_HOLD_OWNER_TRIAGE.md` or operator-chartered equivalent | Explicit operator approval record naming `APPROVED_SCOPE_NAME=cybersecurity_visibility_r001_r002_r007_inventory_recovery_read_only_v0` (or successor) and durable absolute path; must document R-001/R-002/R-007 boundaries; **not** repo-static successor JSONL alone |

**Forbidden as mapping input:** repo-static successor `REPO_STATIC_CYBERSECURITY_RISK_CANDIDATES.jsonl` alone; speculative `CSC-STATIC-v0-*` `candidate_id` substitution; any path under `/tmp` without operator durable archive copy; repo edits that flip pending risks to **mapped** without `INPUT_JSONL_PROVIDED=true` in a future authorized slice.

**Operator token (future mapping slice only):**

```text
INPUT_JSONL=<absolute path to FULL_LOSSLESS_RISK_CANDIDATES.jsonl>
# or, for triage artifact:
INPUT_TRIAGE_ARTIFACT=<absolute path to CYBERSECURITY_POST_HOLD_OWNER_TRIAGE.md>
APPROVED_SCOPE_NAME=cybersecurity_visibility_r001_r002_r007_inventory_recovery_read_only_v0
OPERATOR_NAME=<name>
```

**Gate for definitive mapping:** `NO_MAPPING_WITHOUT_INPUT_ARTIFACT=true` until a future slice records `INPUT_JSONL_PROVIDED=true` (or `INPUT_TRIAGE_ARTIFACT_PROVIDED=true`) with verified artifact checks. Until then, R-001/R-002/R-007 remain **Pending** in the table above with `DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true`.

**Relationship to repo-static charter v0:** Interim histogram and 162-row successor inventory remain **review-input only** per § Pending R-001/R-002/R-007 — repo-static successor inventory charter v0. Successor inventory **cannot** satisfy `INPUT_JSONL_REQUIRED` for definitive mapping.

### Pending R-001/R-002/R-007 — mapping guard v0

```
CYBERSECURITY_VISIBILITY_R_PENDING_MAPPING_GUARD_V0=true
LOSSLESS_JSONL_RECOVERY=false
DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true
INPUT_JSONL_REQUIRED=true
INPUT_JSONL_PROVIDED=false
NO_MAPPING_WITHOUT_INPUT_ARTIFACT=true
FORBIDS_FLIPPING_INPUT_JSONL_PROVIDED_WITHOUT_AUTHORIZED_MAPPING_SLICE=true
FORBIDS_PENDING_RISK_TABLE_MAPPED_STATUS_WITHOUT_INPUT=true
FORBIDS_REPO_STATIC_SUCCESSOR_AS_DEFINITIVE_MAPPING_INPUT=true
CYBERSECURITY_VISIBILITY_R_PENDING_MAPPING_GUARD_DOCS_TESTS_ONLY=true
```

**Purpose:** Static guardrails so pending retained risks **R-001**, **R-002**, and **R-007** cannot be documented or tested as **recovered** or **definitively mapped** while `INPUT_JSONL_PROVIDED=false`. Repo edits that assign `candidate_id`, flip the retained-risk table to **mapped** with a repo test owner, or set `INPUT_JSONL_PROVIDED=true` without an operator-chartered mapping slice are **invalid** in this repository state.

**Non-authorizing:** Same boundaries as § input artifact contract v0; no runtime, workflow dispatch, hooks, Notion, Market, broker/exchange, Testnet/Live, or Master V2 / Double Play authority changes.

### Static visibility contract owners (reuse — do not duplicate)

| Surface | Owner module |
|---------|--------------|
| Workflow secrets/vars/braced contexts (hub) | `tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py` |
| Workflow write permissions | `tests/ci/test_workflow_write_permissions_visibility_contract_v0.py` |
| Workflow network/gh markers | `tests/ci/test_workflow_network_gh_marker_visibility_contract_v0.py` |
| Manual-dispatch sensitive surfaces | `tests/ci/test_workflow_manual_dispatch_sensitive_surface_contract_v0.py` |
| Workflow artifact retention | `tests/ci/test_workflow_artifact_retention_visibility_contract_v0.py` |
| Scheduler boundary hard-block (hub) | `tests/ops/test_scheduler_boundary_hard_block_contract_v0.py` |
| P67/P72 library scheduler boundary opt-in | `tests/ops/test_p67_library_scheduler_boundary_opt_in_v0.py` |
| Workflow permission boundary | `tests/ops/test_workflow_permission_boundary_visibility_v1.py` |
| WebUI API security-header routes | `tests/webui/test_webui_api_security_headers_visibility_contract_v0.py` |
| No `pull_request_target` + checkout v5 pin | `tests/ci/test_workflows_no_pull_request_target_contract_v0.py` |
