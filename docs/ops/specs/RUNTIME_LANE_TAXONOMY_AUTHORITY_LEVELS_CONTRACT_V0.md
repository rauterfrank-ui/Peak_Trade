---
docs_token: DOCS_TOKEN_RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0
status: draft
scope: docs-only, non-authorizing runtime lane taxonomy and authority levels
last_updated: 2026-05-22
---

# Runtime Lane Taxonomy + Authority Levels Contract v0

## 1. Purpose and non-goals

This contract is the **normative lane ID and authority-level index** for Peak_Trade runtime, evidence, planning, and display surfaces. It centralizes taxonomy and cross-links implemented ops tooling (Generic Evidence Run Registry v1, scheduler boundary guards, opt-in primary evidence closeout hooks at canonical owners) without substituting for those owners.

It does **not** authorize runtime, clear HOLD or GLB blockers, grant Live or Testnet permission, or substitute for subsystem owners (preflight retention, GLB register, Canary entry criteria, scheduler daemon policy).

Machine markers (stable literals for contract tests):

```
RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0=true
GENERIC_EVIDENCE_REGISTRY_V1_IMPLEMENTED=true
GENERIC_EVIDENCE_REGISTRY_V1_DEFERRED=false
EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true
TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true
SCHEDULER_BOUNDARY_LAUNCHER_GUARDED=true
P67_CLI_SCHEDULER_BOUNDARY_GUARDED=true
P67_LIBRARY_SCHEDULER_BOUNDARY_OPT_IN_IMPLEMENTED=true
SCHEDULER_LIBRARY_BYPASS_RESIDUAL=true
SCHEDULER_COMPLETION_PRIMARY_EVIDENCE_CLOSEOUT_OPT_IN=true
SUPERVISOR_EVIDENCE_PACK_CLOSEOUT_OPT_IN=true
PRIMARY_EVIDENCE_SHARED_HELPER_REUSED=true
PRIMARY_EVIDENCE_FUTURE_RUN_HARD_GATE_V0=true
FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT=true
TMP_ONLY_EVIDENCE_INVALID=true
MANIFEST_VERIFY_REQUIRED=true
CLOSEOUT_REFERENCE_REQUIRED=true
RUN_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE=true
P79_SUPERVISOR_ARCHIVE_ROOT_MODE_IMPLEMENTED=true
P79_SUPERVISOR_PRIMARY_EVIDENCE_MANIFEST_VERIFY=true
P79_SUPERVISOR_RUNTIME_TICK_MODE_PRESERVED=true
P79_SUPERVISOR_GATE_NON_AUTHORIZING=true
P101_POST_STOP_PRIMARY_EVIDENCE_HINTS_IMPLEMENTED=true
P101_POST_STOP_PACK_HINT_REFERENCED=true
P101_POST_STOP_P79_ARCHIVE_VERIFY_HINT_REFERENCED=true
P101_POST_STOP_HINT_ONLY=true
P101_POST_STOP_PACK_NOT_EXECUTED=true
P101_POST_STOP_P79_VERIFY_NOT_EXECUTED=true
P101_POST_STOP_OPERATOR_EXPLICIT_REQUIRED=true
P101_POST_STOP_EVIDENCE_NON_AUTHORIZING=true
P93_POST_STOP_WRAPPER_HINTS_IMPLEMENTED=true
P93_POST_STOP_WRAPPER_REFERENCED=true
P93_POST_STOP_P79_ARCHIVE_VERIFY_HINT_REFERENCED=true
P93_POST_STOP_HINT_ONLY=true
P93_POST_STOP_WRAPPER_NOT_EXECUTED=true
P93_POST_STOP_PACK_NOT_EXECUTED=true
P93_POST_STOP_P79_VERIFY_NOT_EXECUTED=true
P93_POST_STOP_OPERATOR_EXPLICIT_REQUIRED=true
P93_POST_STOP_EVIDENCE_NON_AUTHORIZING=true
ONLINE_DAEMON_POST_STOP_PACK_WRAPPER_IMPLEMENTED=true
ONLINE_DAEMON_POST_STOP_WRAPPER_OPERATOR_INVOKED=true
ONLINE_DAEMON_POST_STOP_WRAPPER_NO_LAUNCHCTL=true
ONLINE_DAEMON_POST_STOP_WRAPPER_NON_AUTHORIZING=true
MARKET_DASHBOARD_READ_ONLY_NON_AUTHORITY=true
MARKET_DASHBOARD_NO_APPROVAL_AUTHORITY=true
MARKET_DASHBOARD_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true
READINESS_LEDGER_REVIEW_INPUT_ONLY=true
READINESS_MIRROR_NON_AUTHORIZING=true
GATE_SNAPSHOT_NO_APPROVAL_AUTHORITY=true
READINESS_AGGREGATE_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true
MASTER_V2_DOUBLE_PLAY_BOUNDARY_PRESERVED=true
AUTONOMY_STAGE_AUTHORITY_CROSSWALK_V0=true
AUTONOMY_STAGE_COUNT=8
AI_L6_EXEC_FORBIDDEN=true
SIGNAL_NOT_TRADE=true
STRATEGY_NOT_AUTHORITY=true
AI_NOT_AUTHORITY=true
DASHBOARD_NOT_APPROVAL=true
KILLSWITCH_SAFETY_VETO_DOMINATES=true
GO_DECISION_REQUIRES_EXTERNAL_RECORD=true
OPERATOR_ONLY_PERMANENT_GATES_DEFINED=true
REMOTE_RUNTIME_HOST_METADATA_CONTRACT_V0=true
REMOTE_RUNTIME_IS_BACKEND_NOT_LANE=true
REMOTE_RUNTIME_HOST_METADATA_DOCS_TESTS_ONLY=true
S3_FINALIZED_EVIDENCE_TRANSPORT_ONLY=true
NOTION_PROJECTION_NON_AUTHORIZING=true
NOTION_POST_CLOSEOUT_SYNC_PROJECTION_SPEC_V0=true
NOTION_WRITE_DEFAULT=false
NOTION_SYNC_REQUIRES_OPERATOR_TOKEN=true
NOTION_AUTHORITY=false
NOTION_DESTRUCTIVE_OPS=false
REGISTRY_V1_IS_SOLE_NOTION_PROJECTION_FEED=true
MARKET_DASHBOARD_PROJECTION_READONLY=true
MARKET_DASHBOARD_READONLY_RUN_PROJECTION_SPEC_V0=true
MARKET_DASHBOARD_WRITE_DEFAULT=false
MARKET_DASHBOARD_AUTHORITY=false
MARKET_DASHBOARD_RUNTIME_ACTIONS=false
MARKET_DASHBOARD_POLLING_ACTIVE_RUNTIME=false
MARKET_DASHBOARD_START_STOP_BUTTONS=false
MARKET_DASHBOARD_DOUBLE_PLAY_AUTHORITY=false
MARKET_DASHBOARD_DOUBLE_PLAY_TOUCHED=false
REGISTRY_V1_IS_SOLE_DASHBOARD_PROJECTION_FEED=true
S3_FINALIZED_EVIDENCE_EXPORT_GATE_V0=true
S3_FINALIZED_EVIDENCE_EXPORT_IMPLEMENTATION_PREFLIGHT_V0=true
S3_EXPORT_GATE_DOCS_TESTS_ONLY=true
S3_EXPORT_PREFLIGHT_DOCS_TESTS_ONLY=true
S3_EXPORT_DRY_RUN_DEFAULT=true
S3_EXPORT_NO_NETWORK_DEFAULT=true
S3_AUTHORITY=false
S3_UPLOAD_BEFORE_FINALIZE_FORBIDDEN=true
ACTIVE_STAGING_SYNC_FORBIDDEN=true
DOWNLOAD_VERIFY_REQUIRED_BEFORE_CLOSEOUT_ACCEPTANCE=true
MANIFEST_SHA256_REMAINS_CANONICAL=true
SHA256SUMS_STABLE_PARALLEL_TRUTH_FORBIDDEN=true
EVIDENCE_TRANSPORT_DEFAULT=local_only
REMOTE_RUNTIME_V0_LIVE_AUTHORITY=false
REMOTE_RUNTIME_V0_TESTNET_AUTHORITY=false
COMBINED_OUTROOT_COMPOSITION_INDEX_V0=true
COMPOSITION_INDEX_IS_NOT_LANE=true
LANE_ID_DAEMON_PAPER_24H_FORBIDDEN=true
LANE_ID_REMOTE_RUNTIME_FORBIDDEN=true
COMPOSITION_INDEX_AUTHORITY=false
```

Non-goals:

- Mandatory §2a primary-evidence enforcement beyond canonical owner opt-in closeouts (default off)
- Online daemon automatic retention or live-pilot evidence closeout (not implemented in-repo)
- Runtime, adapter, or wrapper execution
- Master V2 / Double Play logic changes
- Go/No-Go approval or gate clearance

## 2. Relationship to existing canonical owners

| Concern | Canonical owner (not replaced) |
|---|---|
| §2a primary evidence retention | [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) §2a |
| §2a.1 future-run primary evidence hard gate | [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) §2a.1 |
| §2b planning artifact retention | [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) §2b |
| Preflight BLOCKED status | [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) |
| GLB-014 / GLB-015 | [MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md](MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md) |
| Canary Live entry | [CANARY_LIVE_ENTRY_CRITERIA.md](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md) |
| Scheduler HOLD boundary | [SCHEDULER_DAEMON.md](../../SCHEDULER_DAEMON.md) |
| Scheduler hard-block contract | [SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md](SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md) |
| Scheduler completion closeout (opt-in) | [run_scheduler.py](../../../scripts/run_scheduler.py) + Preflight §2a |
| Supervisor evidence pack closeout (opt-in, offline) | [pack_online_readiness_supervisor_evidence_v0.py](../../../scripts/ops/pack_online_readiness_supervisor_evidence_v0.py) + Preflight §2a |
| Post-stop pack wrapper (operator-invoked, offline) | [run_online_readiness_post_stop_pack_v0.sh](../../../scripts/ops/run_online_readiness_post_stop_pack_v0.sh) + Preflight §2a |
| P79 archive manifest gate (offline) | [p79_supervisor_health_gate_v1.sh](../../../scripts/ops/p79_supervisor_health_gate_v1.sh) `ARCHIVE_ROOT` + [p79_supervisor_evidence_manifest_verify_v0.py](../../../scripts/ops/p79_supervisor_evidence_manifest_verify_v0.py) |
| P101 post-stop operator hints (non-executing) | [p101_stop_playbook_v1.sh](../../../scripts/ops/p101_stop_playbook_v1.sh) |
| P93 post-stop operator hints (non-executing) | [p93_online_readiness_status_dashboard_v1.sh](../../../scripts/ops/p93_online_readiness_status_dashboard_v1.sh) |
| P91 audit snapshot post-stop wrapper hints (non-executing) | [p91_audit_snapshot_runner_v1.sh](../../../scripts/ops/p91_audit_snapshot_runner_v1.sh) |
| Shared primary evidence finalize helper | [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) |
| Generic Evidence Run Registry v1 | [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) |
| Vocabulary forbidden equalities | [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) |
| OPS Cockpit non-authority | [OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1.md](OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1.md) |
| F5 read-only market dashboard (display) | [FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) |
| Readiness Evidence Ledger v0 | [build_readiness_evidence_ledger_v0.py](../../../scripts/ops/build_readiness_evidence_ledger_v0.py) |
| Readiness Ledger Preflight Mirror v0 | [report_readiness_ledger_preflight_mirror_v0.py](../../../scripts/ops/report_readiness_ledger_preflight_mirror_v0.py) |
| Readiness Gate Snapshot v0 | [report_readiness_gate_snapshot_v0.py](../../../scripts/ops/report_readiness_gate_snapshot_v0.py) |
| Credential boundaries | [RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md](../runbooks/RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md) |
| Autonomy stages 0–7 vocabulary (informative) | [MASTER_V2_GO_LIVE_ROADMAP_V0.md](MASTER_V2_GO_LIVE_ROADMAP_V0.md) §3.1 |
| Decision authority topology | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) |
| Learning/AI/autonomy inventory | [MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md) — **§10** Stage-7 model/policy approval state machine; **§11** learning-change evidence pointer index; **§12** learning-trigger pointer index (Inventory §12; orthogonal; pointer-only; distinct from this spec §12 autonomy crosswalk) |
| AI autonomy layer matrix (L0–L6) | [AI_AUTONOMY_CONTROL_CENTER.md](../control_center/AI_AUTONOMY_CONTROL_CENTER.md) |
| Promotion state machine | [MASTER_V2_PROMOTION_STATE_MACHINE_V1.md](MASTER_V2_PROMOTION_STATE_MACHINE_V1.md) |

**Rule:** This spec is the **lane ID and authority-level index** (including §12 autonomy-stage crosswalk). Retention rules remain in preflight §2a/§2b. Stage vocabulary owner remains roadmap §3.1 — **do not renumber** stages here.

## 3. Normative lane IDs

Each row uses the future registry field names defined in §6.

| lane_id | lane_kind | evidence_role | default authority level |
|---|---|---|---|
| `paper` | bounded_runtime_candidate | primary_runtime | evidence_only |
| `shadow` | bounded_runtime_candidate | primary_runtime | evidence_only |
| `testnet` | bounded_runtime_candidate | primary_runtime | evidence_only |
| `scheduler` | infrastructure | diagnostic_or_composition | planning_only |
| `canary` | governance_docs | external_entry_criteria | planning_only |
| `live_canary` | governance_docs | external_entry_criteria | live_authority_requires_separate_record |
| `live_production` | execution | protected_path | live_authority_forbidden |
| `dashboard` | display | read_model | review_input_only |
| `ai_orchestrator` | advisory | planning_slice | planning_only |
| `notion` | index_pointer | navigation_only | planning_only |
| `docs` | policy | repository_policy | planning_only |

**Paper / Shadow / Testnet hard separation:** Each bounded lane has a distinct adapter, archive path (`runs&#47;paper`, `runs&#47;shadow`, `runs&#47;testnet`), and forbidden cross-lane approval flags. Evidence in one lane does not authorize another.

Non-lane aggregate surfaces (cross-reference only):

- **planning** — §2b durable planning artifacts under `{archive}&#47;planning&#47;`
- **readiness_aggregate** — Readiness Evidence Ledger v0 + Preflight Mirror v0 + Gate Snapshot v0

## 4. Normative authority levels

| authority_level | Meaning |
|---|---|
| `evidence_only` | Primary or bounded runtime evidence verified; no gate clearance |
| `planning_only` | Material planning, closeout, or navigation; not runtime authorization |
| `review_input_only` | Post-run review or display input; operator judgment required |
| `bounded_runtime_candidate` | Lane may compose a bounded run plan; execute still gated |
| `scoped_runtime_exception` | Explicit Stage-3 approval record for one scoped run |
| `operator_decision_required` | Human classification (HOLD, incident stop, GLB clearance) |
| `go_no_go_route_selected` | Named external authority route identified (GLB-014); not Go |
| `go_decision_granted` | External human Go only; never from repo docs or evidence alone |
| `live_authority_forbidden` | Default posture; lane must not imply Live permission |
| `live_authority_requires_separate_record` | Live/Canary requires external LB-APR-001 class record |

`EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true` — no authority level below `go_decision_granted` may start runtime or clear governance blockers by itself.

## 5. Forbidden promotions (normative)

The following promotion literals are **always forbidden** unless an explicit external human record exists where noted:

- `FORBIDDEN_PROMOTION_PAPER_TO_SHADOW_TESTNET_LIVE`
- `FORBIDDEN_PROMOTION_SHADOW_TO_TESTNET_LIVE`
- `FORBIDDEN_PROMOTION_TESTNET_PASS_TO_LIVE_BROKER_EXCHANGE`
- `FORBIDDEN_PROMOTION_SCHEDULER_EVIDENCE_TO_LIVE`
- `FORBIDDEN_PROMOTION_CANARY_DOCS_TO_LIVE`
- `FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL`
- `FORBIDDEN_PROMOTION_SECRET_PRESENCE_TO_CREDENTIAL_VALIDITY`
- `FORBIDDEN_PROMOTION_GO_NO_GO_TEMPLATE_TO_GO_DECISION`

`TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true` — Testnet bounded observation review PASS is prerequisite evidence at most; it is not Live, broker, exchange, or Canary Live permission.

Readiness aggregate verdicts such as `READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE` and `READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE` remain **non-authorizing**; blockers persist.

## 6. Generic Evidence Run Registry v1 field schema (implemented baseline)

```
GENERIC_EVIDENCE_REGISTRY_V1_IMPLEMENTED=true
GENERIC_EVIDENCE_REGISTRY_V1_DEFERRED=false
REGISTRY_V1_LANE_FIELD_SCHEMA_DEFINED=true
```

Implementation owner: `scripts/ops/build_generic_evidence_run_registry_v1.py` (non-authorizing index). Registry PASS does not grant gate clearance or Live/Testnet/broker authority.

Required field names for each lane row in Generic Evidence Run Registry v1:

- `lane_id`
- `lane_kind`
- `evidence_role`
- `runtime_allowed_by_default`
- `requires_approval_record`
- `review_required`
- `manifest_required`
- `durable_retention_required`
- `notion_link_allowed`
- `can_clear_hold`
- `can_clear_glb`
- `can_authorize_live`
- `can_touch_broker_exchange`
- `protected_master_v2_boundary`

Illustrative defaults for `paper`, `shadow`, and `testnet` (all bounded lanes):

| Field | paper / shadow / testnet |
|---|---|
| runtime_allowed_by_default | false |
| requires_approval_record | true |
| review_required | true |
| manifest_required | true |
| durable_retention_required | true |
| notion_link_allowed | index_only |
| can_clear_hold | false |
| can_clear_glb | false |
| can_authorize_live | false |
| can_touch_broker_exchange | false |
| protected_master_v2_boundary | true |

## 6a. Remote Runtime Host Metadata Contract v0 (backend metadata, non-authorizing)

```
REMOTE_RUNTIME_HOST_METADATA_CONTRACT_V0=true
REMOTE_RUNTIME_IS_BACKEND_NOT_LANE=true
REMOTE_RUNTIME_HOST_METADATA_DOCS_TESTS_ONLY=true
S3_FINALIZED_EVIDENCE_TRANSPORT_ONLY=true
NOTION_PROJECTION_NON_AUTHORIZING=true
MARKET_DASHBOARD_PROJECTION_READONLY=true
REMOTE_RUNTIME_V0_LIVE_AUTHORITY=false
REMOTE_RUNTIME_V0_TESTNET_AUTHORITY=false
REGISTRY_V1_REMOTE_RUNTIME_HOST_METADATA_FIELDS_DEFINED=true
REGISTRY_V1_SECTION_6A_FIELDS_POPULATED=true
```

**Purpose:** Describe where a bounded `paper` / `shadow` run executes (local laptop vs remote host) and how finalized evidence may be transported or projected — **without** creating a new lane, scheduler authority, evidence standard, or closeout standard.

**Normative rule:** Remote Runtime is **backend metadata** for existing bounded lanes (`paper`, `shadow`, `testnet`). It is **not** a new `lane_id`. Remote hosts run the **same** canonical adapters, scheduler boundary guards, approval records, and `primary_evidence_retention_v0` manifest rules as local hosts.

Implementation index (Registry v1 emits §6a fields as non-authorizing metadata defaults):

- Constants owner: [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) — `REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS` merged into every `runs[]` and `compositions[]` record (`REGISTRY_V1_SECTION_6A_FIELDS_POPULATED=true`). Defaults remain `runtime_host=local`, `runtime_backend=laptop`, `evidence_transport=local_only`, `notion_projection=disabled`, `market_dashboard_projection=disabled`, `live_authority=false`, `testnet_authority=false` unless explicit future operator metadata opts in. Archive presence alone does **not** infer remote runtime, S3 export, Notion sync, or dashboard projection.
- Manifest owner unchanged: [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) — `MANIFEST.sha256` remains the sole primary evidence manifest format.
- Preflight / bounded gate owner unchanged: [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) §2a/§2a.1.

### Optional Generic Evidence Run Registry v1 run-row fields (v0)

These fields are **metadata only**. They do **not** authorize runtime, clear HOLD, or grant Live/Testnet/broker permission.

| Field | Allowed values (v0) | Default (v0) |
|---|---|---|
| `runtime_host` | `local` \| `remote` | `local` |
| `runtime_backend` | `laptop` \| `ec2` \| `vps` \| `data_node` \| `gha_runner` | `laptop` |
| `runtime_mode` | `paper_only` \| `paper_then_shadow` | `paper_only` |
| `evidence_root_type` | `local_durable` \| `remote_durable` | `local_durable` |
| `evidence_transport` | `local_only` \| `s3_export_after_finalize` | `local_only` |
| `notion_projection` | `disabled` \| `post_closeout_sync` \| `verified_evidence_index` | `disabled` |
| `market_dashboard_projection` | `disabled` \| `read_only_run_status` \| `read_only_evidence_status` | `disabled` |
| `live_authority` | `false` only in v0 | `false` |
| `testnet_authority` | `false` only in v0 | `false` |

**Forbidden:** introducing `lane_id=remote_runtime`, `remote_runtime`, or any parallel remote lane in taxonomy §3 or registry lane catalog.

### Backend-not-lane semantics

- `runtime_host=remote` changes **host placement only**; `lane_id` remains `paper`, `shadow`, or `testnet`.
- Remote execution must reuse existing bounded adapters ([run_paper_only_bounded_observation_adapter_v0.py](../../../scripts/ops/run_paper_only_bounded_observation_adapter_v0.py), [run_shadow_bounded_observation_adapter_v0.py](../../../scripts/ops/run_shadow_bounded_observation_adapter_v0.py)) and scheduler hard-block contracts (§7).
- [REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md](REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md) Class B (durable daemon) is **host/backend planning** atop the same gates — not a separate authority surface.

### S3 / Object Storage — finalized evidence transport only

```
S3_FINALIZED_EVIDENCE_TRANSPORT_ONLY=true
TMP_ONLY_EVIDENCE_INVALID=true
MANIFEST_VERIFY_REQUIRED=true
```

- `evidence_transport=s3_export_after_finalize` is permitted **only after** `finalize_primary_evidence_root()` / `verify_manifest_sha256()` returns success on the durable root (`MANIFEST.sha256` RC=0).
- S3/Object Storage is **transport/archive**, not active staging sync, not a second evidence standard, and not closeout acceptance by itself.
- Consumer-side download + manifest verify is required before treating remote copies as primary evidence ([PHASE_W_EXPORT_PACK_GH_CONSUMER.md](../runbooks/PHASE_W_EXPORT_PACK_GH_CONSUMER.md) patterns may be **extended** to `MANIFEST.sha256`; do not replace with a parallel manifest scheme).
- [PHASE_T_DATA_NODE_EXPORT_CHANNEL.md](../runbooks/PHASE_T_DATA_NODE_EXPORT_CHANNEL.md) remains **planning-only / candidate-to-extend** for export prefixes; bounded run finalized evidence uses `run_id`-scoped keys under a `finalized_evidence&#47;` prefix (proposal only in v0).

### Notion — projection/index only

```
NOTION_PROJECTION_NON_AUTHORIZING=true
```

- `notion_projection=post_closeout_sync` or `verified_evidence_index` may copy **pointers** (run_id, durable archive path, manifest verify RC, review verdicts) after closeout — **never** gate clearance or approval.
- Taxonomy `lane_id=notion` remains `navigation_only` / `planning_only` (§3).
- `FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL` applies (§5).
- Notion writes require an explicit operator post-closeout token; default `disabled`.

### 6a.1 Notion post-closeout sync projection contract v0

```
NOTION_POST_CLOSEOUT_SYNC_PROJECTION_SPEC_V0=true
NOTION_PROJECTION_NON_AUTHORIZING=true
NOTION_WRITE_DEFAULT=false
NOTION_SYNC_REQUIRES_OPERATOR_TOKEN=true
NOTION_AUTHORITY=false
NOTION_DESTRUCTIVE_OPS=false
RUNTIME_AUTHORITY=false
SCHEDULER_CLEARANCE_AUTHORITY=false
LIVE_AUTHORITY=false
TESTNET_AUTHORITY=false
BROKER_AUTHORITY=false
DOUBLE_PLAY_AUTHORITY=false
REGISTRY_V1_IS_SOLE_NOTION_PROJECTION_FEED=true
NOTION_PROJECTION_DEFAULT=disabled
```

**Purpose:** Define how future Notion post-closeout sync may project **non-authorizing** evidence index rows from Generic Evidence Run Registry v1 — **without** creating a Notion truth layer, **without** Notion writes in this slice, and **without** parsing durable archives ad hoc.

**Canonical feed (sole source):** [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) JSON output (`schema=peak_trade.generic_evidence_run_registry.v1`): `runs[]`, `compositions[]`, top-level `verdict`, `issues`, `blockers`, `archive_root`, and §6a metadata on each record. **Do not** walk `DURABLE_ARCHIVE_ROOT` directly for Notion projection.

#### `notion_projection` states (Registry v1 §6a field)

| State | Meaning (v0) |
|---|---|
| `disabled` | **Default.** No Notion sync; projection contract inactive. |
| `post_closeout_sync` | Future operator-token-gated sync may copy pointer fields after closeout only. |
| `verified_evidence_index` | Future operator-token-gated sync may index verified registry rows only (still non-authorizing). |

Default: `notion_projection=disabled` on every `runs[]` and `compositions[]` record until explicit future operator metadata opts in.

#### Future sync gate (default off)

- Notion sync requires explicit operator token: `APPROVE_NOTION_POST_CLOSEOUT_SYNC_NOW=true` (future slice; **not implemented** in this contract).
- Token may authorize **projection write only** — never runtime, testnet, live, scheduler, broker, exchange, strategy, or Double Play clearance.
- Default is **no sync** (`NOTION_WRITE_DEFAULT=false`).

#### Allowed projection fields (pointers only)

From Registry v1 `runs[]` / `compositions[]` rows only:

- `run_id`, `lane_id` or `composition_id`, `record_kind`
- §6a: `runtime_host`, `runtime_backend`, `runtime_mode`, `evidence_root_type`, `evidence_transport`, `notion_projection`, `market_dashboard_projection`
- `evidence_status`, `review_verdict`, `manifest_verified` (or `rollup_manifest_verified` on compositions)
- `archive_path` pointer (relative under `archive_root`)
- Top-level registry `verdict`, summarized `issues` / `blockers` (codes only; no secret values)
- Closeout pointer **if already present in registry-derived summary** (future projection slice; not inferred by walking archive)
- Authority markers as explicit **false** / non-authorizing literals

Composition records: include `child_lane_refs` / `child_lane_status` pointers only; composition index does **not** substitute for per-lane primary evidence.

#### Forbidden Notion behavior

- No secrets, AWS credentials, exchange&#47;broker credentials
- No destructive operations (delete, archive move) without separate explicit operator charter
- No approval authority, runtime start&#47;stop, scheduler clearance, testnet&#47;live&#47;broker&#47;strategy&#47;Double Play authority
- No parallel Notion truth layer; repo contracts, manifests, closeouts, and operator approvals remain canonical
- No `lane_id=daemon_paper_24h`, no `lane_id=remote_runtime`, no Registry v2

#### Status interpretation

- Notion may display imported registry `verdict` values (`GENERIC_EVIDENCE_RUN_REGISTRY_PASS_BLOCKED_SAFE`, `GENERIC_EVIDENCE_RUN_REGISTRY_REVIEW_REQUIRED`, `GENERIC_EVIDENCE_RUN_REGISTRY_FAIL_CLOSED`) as **projection status only**.
- Notion status does **not** clear blockers, override manifests&#47;closeouts, or grant gates.
- `FAIL_CLOSED` remains fail-closed even if a Notion page exists.

#### Canonical boundary copy (required on future Notion database)

> This Notion database is a non-authorizing projection of Peak_Trade repo&#47;evidence state. Repo contracts, manifests, closeouts, and explicit operator approvals remain canonical. Notion entries do not authorize runtime, testnet, live trading, broker access, strategy execution, scheduler clearance, or Double Play decisions.

Cross-reference: Remote Runtime Host Metadata §6a backend-not-lane semantics; composition-index §6b for `paper_then_shadow` pointer rows.

### 6a.2 Market Dashboard read-only run projection contract v0

```
MARKET_DASHBOARD_READONLY_RUN_PROJECTION_SPEC_V0=true
MARKET_DASHBOARD_PROJECTION_READONLY=true
MARKET_DASHBOARD_READ_ONLY_NON_AUTHORITY=true
MARKET_DASHBOARD_NO_APPROVAL_AUTHORITY=true
MARKET_DASHBOARD_WRITE_DEFAULT=false
MARKET_DASHBOARD_AUTHORITY=false
MARKET_DASHBOARD_RUNTIME_ACTIONS=false
MARKET_DASHBOARD_POLLING_ACTIVE_RUNTIME=false
MARKET_DASHBOARD_START_STOP_BUTTONS=false
MARKET_DASHBOARD_DOUBLE_PLAY_AUTHORITY=false
MARKET_DASHBOARD_DOUBLE_PLAY_TOUCHED=false
RUNTIME_AUTHORITY=false
SCHEDULER_CLEARANCE_AUTHORITY=false
LIVE_AUTHORITY=false
TESTNET_AUTHORITY=false
BROKER_AUTHORITY=false
DOUBLE_PLAY_AUTHORITY=false
REGISTRY_V1_IS_SOLE_DASHBOARD_PROJECTION_FEED=true
MARKET_DASHBOARD_PROJECTION_DEFAULT=disabled
```

**Purpose:** Define how future Market Dashboard read-only surfaces may project **non-authorizing** run/evidence status from Generic Evidence Run Registry v1 — **without** creating a Dashboard truth layer, **without** UI/rendering in this slice, **without** polling active runtime, **without** runtime start&#47;stop controls, and **without** parsing durable archives ad hoc.

**Canonical feed (sole source):** [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) JSON output (`schema=peak_trade.generic_evidence_run_registry.v1`): `runs[]`, `compositions[]`, top-level `verdict`, `issues`, `blockers`, `archive_root`, and §6a metadata on each record. **Do not** walk `DURABLE_ARCHIVE_ROOT` directly for Dashboard projection.

#### `market_dashboard_projection` states (Registry v1 §6a field)

| State | Meaning (v0) |
|---|---|
| `disabled` | **Default.** No registry-derived run/evidence projection on dashboard surfaces. |
| `read_only_run_status` | Future read-only display may show run pointer + status labels from Registry v1 only. |
| `read_only_evidence_status` | Future read-only display may show evidence/manifest/review status from Registry v1 only. |

Default: `market_dashboard_projection=disabled` on every `runs[]` and `compositions[]` record until explicit future operator metadata opts in.

#### Registry v1 sole feed (no ad hoc archive walks)

Consumers may read Registry v1 JSON or registry-derived read-only artifacts only:

- `runs[]`, `compositions[]`, §6a metadata fields
- `evidence_status`, `review_verdict`, `manifest_verified` (or `rollup_manifest_verified` on compositions)
- `archive_path` / top-level `archive_root` pointers
- `child_lane_refs` / `child_lane_status` on composition records (pointers only)
- Top-level `verdict`, summarized `issues` / `blockers` (codes only; no secret values)
- Closeout pointer **if already present in registry-derived summary** (not inferred by walking archive)
- Freshness/status labels **only** when derived from Registry v1 timestamps (e.g. `built_at`) — never from live runtime polling

#### Allowed Dashboard projection fields (pointers/status only)

From Registry v1 `runs[]` / `compositions[]` rows only:

- `run_id`, `lane_id` or `composition_id`, `record_kind`
- §6a: `runtime_host`, `runtime_backend`, `runtime_mode`, `evidence_root_type`, `evidence_transport`, `notion_projection`, `market_dashboard_projection`
- `evidence_status`, `review_verdict`, `manifest_verified` (or `rollup_manifest_verified` on compositions)
- `archive_path` pointer (relative under `archive_root`)
- Top-level registry `verdict`, summarized `issues` / `blockers`
- Closeout pointer if present in registry-derived summary
- Authority markers as explicit **false** / non-authorizing literals

Composition records: include `child_lane_refs` / `child_lane_status` pointers only; composition index does **not** substitute for per-lane primary evidence.

#### Forbidden Dashboard behavior

- No runtime starts, runtime stops, scheduler clearance, or strategy execution
- No polling active runtime, no start&#47;stop buttons, no runtime actions from Dashboard
- No AWS CLI, rclone, S3 uploads, or Notion writes from Dashboard projection paths
- No broker&#47;exchange authority, testnet&#47;live authority, approval authority, or Double Play / Master V2 authority
- No parallel Dashboard truth layer; repo contracts, manifests, closeouts, and operator approvals remain canonical
- No changes to `GET &#47;market&#47;double-play` routes, handlers, templates, or decision authority (`MARKET_DASHBOARD_DOUBLE_PLAY_TOUCHED=false`)
- No `lane_id=daemon_paper_24h`, no `lane_id=remote_runtime`, no Registry v2

#### Status interpretation

- Dashboard may display imported registry `verdict` values (`GENERIC_EVIDENCE_RUN_REGISTRY_PASS_BLOCKED_SAFE`, `GENERIC_EVIDENCE_RUN_REGISTRY_REVIEW_REQUIRED`, `GENERIC_EVIDENCE_RUN_REGISTRY_FAIL_CLOSED`) as **projection status only**.
- Dashboard status does **not** clear blockers, override manifests&#47;closeouts, or grant gates.
- `FAIL_CLOSED` remains fail-closed even if displayed on a read-only surface.

#### Surface boundaries (orthogonal owners)

- **`GET &#47;market` only** for future registry-derived run/evidence projection overlays: [MARKET_SURFACE_V0.md](../../webui/MARKET_SURFACE_V0.md) remains the canonical Market Surface v0 owner (SSR OHLCV/dummy/kraken read-only lineage).
- **F5 futures read-only display** remains orthogonal: [FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) — instrument/provenance/risk display semantics; **does not** replace Registry v1 run/evidence projection fields.
- **`GET &#47;market&#47;double-play` untouched:** Master V2 / Double Play read-only composition route, handlers, templates, and authority boundaries remain unchanged (§9). Registry projection must **not** embed Double Play decision or selection authority.

Detail owner for existing F5 / §7h display markers: taxonomy §7h and [FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md).

#### Canonical boundary copy (required on future dashboard projection surfaces)

> Read-only operational projection. This dashboard does not authorize runtime, scheduler clearance, testnet, live trading, broker access, strategy execution, S3 export, Notion sync, or Double Play decisions.

Cross-reference: Notion projection §6a.1 (shared Registry v1 feed semantics); Remote Runtime Host Metadata §6a backend-not-lane semantics; composition-index §6b for `paper_then_shadow` pointer rows.

### 6a.3 S3 finalized evidence export gate contract v0

```
S3_FINALIZED_EVIDENCE_EXPORT_GATE_V0=true
S3_FINALIZED_EVIDENCE_TRANSPORT_ONLY=true
S3_EXPORT_GATE_DOCS_TESTS_ONLY=true
TMP_ONLY_EVIDENCE_INVALID=true
MANIFEST_VERIFY_REQUIRED=true
S3_AUTHORITY=false
S3_UPLOAD_BEFORE_FINALIZE_FORBIDDEN=true
ACTIVE_STAGING_SYNC_FORBIDDEN=true
DOWNLOAD_VERIFY_REQUIRED_BEFORE_CLOSEOUT_ACCEPTANCE=true
MANIFEST_SHA256_REMAINS_CANONICAL=true
SHA256SUMS_STABLE_PARALLEL_TRUTH_FORBIDDEN=true
RUNTIME_AUTHORITY=false
SCHEDULER_CLEARANCE_AUTHORITY=false
LIVE_AUTHORITY=false
TESTNET_AUTHORITY=false
BROKER_AUTHORITY=false
NOTION_AUTHORITY=false
MARKET_DASHBOARD_AUTHORITY=false
DOUBLE_PLAY_AUTHORITY=false
EVIDENCE_TRANSPORT_DEFAULT=local_only
```

**Purpose:** Define when Registry v1 may represent `evidence_transport=s3_export_after_finalize` and when a remote/object-storage copy may be **accepted** for closeout/review — **without** S3 upload/download implementation in this slice, **without** AWS/rclone calls, and **without** a parallel manifest truth layer.

**Canonical owners (reuse):**

- Finalize + manifest verify: [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) — `finalize_primary_evidence_root()`, `MANIFEST.sha256`
- Registry v1 metadata: [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) — §6a `evidence_transport`, `manifest_verified`, `evidence_status`
- Projection consumer fixtures: [projection_consumer_v0.py](../../../tests/fixtures/ops/generic_evidence_run_registry_v1/projection_consumer_v0.py) — `S3_RELEVANT_PROJECTION_FIELDS`
- Extend-only planning surfaces: [PHASE_T_DATA_NODE_EXPORT_CHANNEL.md](../runbooks/PHASE_T_DATA_NODE_EXPORT_CHANNEL.md), [PHASE_W_EXPORT_PACK_GH_CONSUMER.md](../runbooks/PHASE_W_EXPORT_PACK_GH_CONSUMER.md) — may be extended; **do not** replace `MANIFEST.sha256` with `SHA256SUMS.stable.txt` as competing truth (§6b)

#### `evidence_transport` states (Registry v1 §6a field)

| State | Meaning (v0) |
|---|---|
| `local_only` | **Default.** Evidence remains local/durable; no finalized S3 export representation. |
| `s3_export_after_finalize` | Future operator-gated export may occur **only after** finalize + `MANIFEST.sha256` verify RC=0 on durable primary evidence. |

Default: `evidence_transport=local_only` on every `runs[]` and `compositions[]` record until explicit future operator metadata opts in **and** export eligibility preconditions are met.

#### Export eligibility (all required)

Before `evidence_transport=s3_export_after_finalize` may appear on a Registry v1 row or export planning surface:

1. Durable primary evidence root exists **outside** `/tmp` (non-staging).
2. `finalize_primary_evidence_root()` completed on that root.
3. `MANIFEST.sha256` exists at the canonical per-lane or composition-rollup path (§6b manifest resolution).
4. `MANIFEST.sha256` verify returns **RC=0** (`manifest_verified=true` on lane rows, or `rollup_manifest_verified=true` on composition records where applicable).
5. Active staging sync is **forbidden** — no live `/tmp` → remote mirror during runtime.
6. Runtime process has ended **or** the lane/composition evidence root is finalized for export (closeout boundary reached).

Registry v1 JSON is the metadata index only; **do not** infer export eligibility by walking remote buckets ad hoc.

#### Consumer acceptance (remote copy)

- S3/Object Storage copy is **not** accepted as primary evidence until downloaded/re-materialized locally.
- Local download + verify against **`MANIFEST.sha256`** must pass (RC=0).
- Closeout acceptance of a remote copy requires **download+verify RC=0** — upload success alone is insufficient.
- `SHA256SUMS.stable.txt` must **not** substitute for or compete with `MANIFEST.sha256` (§6b forbidden promotions).

#### Allowed S3 projection / registry pointer fields

From Registry v1 `runs[]` / `compositions[]` and top-level summary only (shared with Notion/Dashboard consumers):

- `run_id`, `lane_id` or `composition_id`, `record_kind`
- `evidence_transport`, `evidence_status`, `manifest_verified` (or `rollup_manifest_verified` on compositions)
- `archive_path`, top-level `archive_root`
- Top-level `verdict`, summarized `issues` / `blockers` (codes only)
- §6a metadata pointers as non-authorizing literals

#### Forbidden S3 behavior

- No runtime, scheduler, approval, testnet, live, broker, exchange, or strategy execution authority
- No Notion sync authority, Market Dashboard status authority, or Double Play / Master V2 authority
- No upload before finalization; no active staging sync
- No closeout acceptance without download+verify
- No secrets or credentials in Registry / Notion / Dashboard projections
- No `SHA256SUMS.stable.txt` as parallel truth or authority
- No `lane_id=daemon_paper_24h`, no `lane_id=remote_runtime`, no Registry v2

#### Canonical boundary copy (required on future S3/export surfaces)

> S3/Object Storage is finalized evidence transport only. S3 objects, prefixes, upload success, or dashboard/notion links do not authorize runtime, scheduler clearance, testnet, live trading, broker access, strategy execution, Notion sync, Dashboard status, or Double Play decisions. MANIFEST.sha256 remains canonical for evidence verification.

Cross-reference: Notion projection §6a.1; Market Dashboard projection §6a.2; composition-index §6b; Remote Runtime Host Metadata §6a backend-not-lane semantics.

### 6a.3.1 S3 finalized evidence export implementation preflight contract v0

```
S3_FINALIZED_EVIDENCE_EXPORT_IMPLEMENTATION_PREFLIGHT_V0=true
S3_EXPORT_PREFLIGHT_DOCS_TESTS_ONLY=true
S3_EXPORT_DRY_RUN_DEFAULT=true
S3_EXPORT_NO_NETWORK_DEFAULT=true
S3_FINALIZED_EVIDENCE_TRANSPORT_ONLY=true
MANIFEST_SHA256_REMAINS_CANONICAL=true
SHA256SUMS_STABLE_PARALLEL_TRUTH_FORBIDDEN=true
PHASE_T_W_EXTEND_ONLY=true
PHASE_T_W_RECONCILED_TO_MANIFEST_SHA256=true
S3_UPLOAD_BEFORE_FINALIZE_FORBIDDEN=true
ACTIVE_STAGING_SYNC_FORBIDDEN=true
DOWNLOAD_VERIFY_REQUIRED_BEFORE_CLOSEOUT_ACCEPTANCE=true
S3_AUTHORITY=false
RUNTIME_AUTHORITY=false
SCHEDULER_CLEARANCE_AUTHORITY=false
LIVE_AUTHORITY=false
TESTNET_AUTHORITY=false
BROKER_AUTHORITY=false
NOTION_AUTHORITY=false
MARKET_DASHBOARD_AUTHORITY=false
DOUBLE_PLAY_AUTHORITY=false
EVIDENCE_TRANSPORT_DEFAULT=local_only
LOCAL_ONLY_DRY_ADAPTER_CONTRACT_DOCUMENTED=true
```

**Purpose:** Define a **non-executing** implementation preflight for a future local-only S3 finalized-evidence export dry adapter or CLI command contract. This slice bridges §6a.3 gate rules to extend-only Phase T/W planning surfaces — **without** AWS/rclone calls, **without** upload/download, **without** a parallel manifest truth layer, and **without** mutating durable archives.

**Canonical owners (reuse):**

- Gate contract: §6a.3 above (export eligibility + consumer acceptance)
- Finalize + manifest verify: [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) — `finalize_primary_evidence_root()`, `verify_manifest_sha256()`, `MANIFEST.sha256`
- Registry v1 metadata: [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) — §6a fields; constants `S3_FINALIZED_EVIDENCE_EXPORT_IMPLEMENTATION_PREFLIGHT_V0`
- Projection consumer fixtures: [projection_consumer_v0.py](../../../tests/fixtures/ops/generic_evidence_run_registry_v1/projection_consumer_v0.py) — `S3_RELEVANT_PROJECTION_FIELDS`
- Extend-only Phase surfaces: [PHASE_T_DATA_NODE_EXPORT_CHANNEL.md](../runbooks/PHASE_T_DATA_NODE_EXPORT_CHANNEL.md), [PHASE_W_EXPORT_PACK_GH_CONSUMER.md](../runbooks/PHASE_W_EXPORT_PACK_GH_CONSUMER.md)

#### Future local-only dry adapter / command contract shape (not implemented in v0)

A future governed slice may introduce a **local-only, non-network** preflight command (working name: `preflight_s3_finalized_evidence_export_v0`) with the following contract shape:

| Input / flag | Required | Semantics (v0) |
|---|---|---|
| `--durable-evidence-root` | yes | Absolute path to finalized durable primary evidence root (**outside** `/tmp`) |
| `--registry-json` | yes | Path to Registry v1 JSON (`schema=peak_trade.generic_evidence_run_registry.v1`) |
| `--run-id` | yes | Target run row in `runs[]` or composition row in `compositions[]` |
| `--lane-id` or `--composition-id` | one required | Lane row vs composition-index row context |
| `--manifest-sha256` | default derived | Explicit path to canonical `MANIFEST.sha256` (per-lane or composition rollup per §6b) |
| `--export-prefix-plan` | planning only | Non-executing S3 prefix proposal (e.g. `finalized_evidence&#47;{run_id}&#47;`); **does not** upload |
| `--dry-run` | default `true` | Preflight emits checklist + exit code only; no side effects |
| `--no-network` | default `true` | Hard forbid AWS/rclone/upload/download in preflight path |

**Output (preflight-only):** structured pass/fail checklist, blocker codes, and optional Registry v1 metadata **recommendation** for `evidence_transport=s3_export_after_finalize` — never auto-applied without operator gate in a future slice.

Default posture: `S3_EXPORT_DRY_RUN_DEFAULT=true`, `S3_EXPORT_NO_NETWORK_DEFAULT=true`. Preflight **never** executes upload, download, runtime, or scheduler actions.

#### Preflight checklist (all required for export-ready recommendation)

Before a future dry adapter may recommend `evidence_transport=s3_export_after_finalize`:

1. `durable-evidence-root` is **outside** `/tmp` (non-staging).
2. `finalize_primary_evidence_root()` completed on that root.
3. `MANIFEST.sha256` exists at the resolved per-lane or composition-rollup path.
4. `MANIFEST.sha256` verify returns **RC=0** (`manifest_verified=true` or `rollup_manifest_verified=true`).
5. Registry row shows `evidence_transport=local_only` **before** export representation (transition gated).
6. Active staging sync is **absent** — no live `/tmp` → remote mirror.
7. Runtime process has ended **or** lane/composition evidence root is finalized for export.
8. No secrets, AWS credentials, or broker/exchange credentials appear in Registry JSON or projection outputs.

Fail-closed: any checklist failure → preflight RC≠0; do **not** recommend export or set `s3_export_after_finalize`.

#### PHASE_T / PHASE_W reconciliation (extend-only)

Phase T/W runbooks predate bounded primary-evidence `MANIFEST.sha256` closeout. Reconciliation rules for future implementation:

| Legacy Phase surface | v0 reconciliation rule |
|---|---|
| [PHASE_T_DATA_NODE_EXPORT_CHANNEL.md](../runbooks/PHASE_T_DATA_NODE_EXPORT_CHANNEL.md) `manifest.json` + `SHA256SUMS.stable.txt` | **Extend-only.** Future Phase T export packs for bounded runs must treat `MANIFEST.sha256` from `primary_evidence_retention_v0` as **canonical**. Legacy filenames may appear only as **non-authoritative compatibility artifacts** that point back to `MANIFEST.sha256`. |
| [PHASE_W_EXPORT_PACK_GH_CONSUMER.md](../runbooks/PHASE_W_EXPORT_PACK_GH_CONSUMER.md) `sha256sum -c SHA256SUMS.stable.txt` | **Extend-only.** Future Phase W consumers for bounded finalized evidence must verify against **`MANIFEST.sha256`** (RC=0). `SHA256SUMS.stable.txt` must **not** become competing truth or closeout authority. |

```
PHASE_T_W_EXTEND_ONLY=true
PHASE_T_W_RECONCILED_TO_MANIFEST_SHA256=true
MANIFEST_SHA256_REMAINS_CANONICAL=true
SHA256SUMS_STABLE_PARALLEL_TRUTH_FORBIDDEN=true
```

Do **not** modify Phase T/W to replace `MANIFEST.sha256`. Do **not** introduce `SHA256SUMS.stable.txt` as parallel truth in new bounded-evidence paths.

#### Export eligibility transition (`local_only` → `s3_export_after_finalize`)

- `evidence_transport=s3_export_after_finalize` may be **represented** only after §6a.3 export eligibility **and** this preflight checklist pass.
- Upload success, object prefix existence, or bucket listing **do not** imply closeout acceptance or approval authority.
- Object prefix is a **transport plan pointer** only — not scheduler clearance, not testnet/live gate, not operator approval.

#### Consumer acceptance (remote copy; unchanged from §6a.3)

- Remote/object-storage copy must be downloaded or re-materialized locally before review.
- Local download + verify against **`MANIFEST.sha256`** must return RC=0.
- Failed download verify is **fail-closed** — remote copy rejected for closeout acceptance.
- Upload success alone is insufficient.

#### Forbidden (implementation preflight + future adapter)

- Upload before finalize; active staging sync; acceptance without download+verify
- Secrets/credentials in Registry / Notion / Dashboard projections
- Runtime, scheduler clearance, live/testnet/broker/exchange/strategy authority
- Notion sync authority; Market Dashboard status authority; Double Play / Master V2 authority
- Registry v2; new lane; `lane_id=daemon_paper_24h`; `lane_id=remote_runtime`
- AWS CLI, rclone, S3 upload/download execution in this preflight slice
- `SHA256SUMS.stable.txt` as parallel truth or authority

#### Canonical boundary copy (required on future preflight/adapter surfaces)

> S3 export implementation preflight is non-executing. It authorizes no upload, download, runtime, scheduler clearance, testnet, live trading, broker access, strategy execution, Notion sync, Dashboard status, or Double Play decisions. MANIFEST.sha256 remains canonical.

Cross-reference: §6a.3 gate contract; Notion projection §6a.1; Market Dashboard projection §6a.2; composition-index §6b; Remote Runtime Host Metadata §6a backend-not-lane semantics.

### v0 authority posture (hard false)

```
REMOTE_RUNTIME_V0_LIVE_AUTHORITY=false
REMOTE_RUNTIME_V0_TESTNET_AUTHORITY=false
live_authority=false
testnet_authority=false
```

Remote Runtime Host Metadata v0 does **not** authorize Live trading, Testnet execution, broker/exchange access, strategy execution, scheduler global clearance, or Double Play decisions.

### Illustrative evidence anchor (non-authorizing example only)

Completed bounded dry-run (example context for field semantics only):

- `RUN_ID=daemon_paper_24h_20260524T205447Z`
- Durable archive (operator path): external `Peak_Trade_runtime_evidence_archive_*` with `MANIFEST_VERIFY_RC=0`
- Combined sequence: `paper_then_shadow` with reviews PASS — documents **field usage**, not gate clearance for future runs.

### Reuse-before-new

Do **not** add a parallel remote-runtime runbook, remote lane, remote evidence manifest, remote closeout standard, or remote scheduler authority. Extend this §6a, Generic Evidence Run Registry v1 optional fields, and existing Phase T/W export consumer planning only.

### 6b. Combined OUTROOT composition-index v0 (not a lane)

```
COMBINED_OUTROOT_COMPOSITION_INDEX_V0=true
COMPOSITION_INDEX_IS_NOT_LANE=true
LANE_ID_DAEMON_PAPER_24H_FORBIDDEN=true
LANE_ID_REMOTE_RUNTIME_FORBIDDEN=true
COMPOSITION_INDEX_AUTHORITY=false
composition_index_authority=false
live_authority=false
testnet_authority=false
s3_authority=false
notion_authority=false
market_dashboard_authority=false
REGISTRY_V1_COMPOSITION_RECORD_KIND=composition_index
PER_LANE_MANIFEST_SHA256_REMAINS_CANONICAL=true
```

**Purpose:** Represent combined daemon paper+shadow OUTROOTs as **composition/index metadata** in Generic Evidence Run Registry v1 without promoting `runs&#47;daemon_paper_24h&#47;` to a taxonomy lane or introducing `lane_id=daemon_paper_24h`.

**Normative rule:** `paper`, `shadow`, and `testnet` remain the only bounded primary-evidence **lanes** (§3). A combined OUTROOT under `runs&#47;daemon_paper_24h&#47;{run_id}&#47;` is a **composition wrapper** that references child lane rows; it is **not** a runtime lane, approval lane, evidence standard, or closeout standard.

Implementation index:

- Registry builder: [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) — `compositions[]` records with `record_kind=composition_index`; lane rows remain in `runs[]`.
- Per-lane primary evidence owner unchanged: [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) — `MANIFEST.sha256` at `runs&#47;{paper,shadow,testnet}&#47;{run_id}&#47;`.
- Preflight §2a anchor: [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) — per-lane manifest verify remains canonical.

#### composition_index vs lane_id

| Surface | Role | Authority |
|---|---|---|
| `lane_id` ∈ {`paper`, `shadow`, `testnet`} | Canonical bounded primary-evidence lane | `evidence_only` (§3) |
| `composition_id=daemon_paper_24h` | Combined OUTROOT index wrapper | **none** (`composition_index_authority=false`) |
| `lane_id=daemon_paper_24h` | **Forbidden** | must not appear in registry lane catalog |
| `lane_id=remote_runtime` | **Forbidden** (§6a) | backend metadata only |

#### paper_then_shadow composition semantics

- `runtime_mode=paper_then_shadow` on a composition record documents sequencing context only.
- Composition record **`child_lane_refs`** point at canonical lane run roots: `runs&#47;paper&#47;{run_id}&#47;`, `runs&#47;shadow&#47;{run_id}&#47;`.
- Child lane rows in `runs[]` remain authoritative for lane primary evidence, review verdicts, and closeout artifacts.
- Composition record may carry governance/context pointers; it does **not** substitute for per-lane evidence or clear gates.

#### Manifest resolution

- **Per-lane primary:** `runs&#47;{lane}&#47;{run_id}&#47;MANIFEST.sha256` — sole canonical primary evidence manifest for that lane (Preflight §2a; unchanged).
- **Composition rollup (optional):** `runs&#47;daemon_paper_24h&#47;{run_id}&#47;manifests&#47;MANIFEST.sha256` — composition rollup only; paths relative to the composition root.
- Composition rollup manifest **does not replace** per-lane `MANIFEST.sha256`.
- Root-level `MANIFEST.sha256` on a composition OUTROOT is **not** primary evidence; registry emits `COMPOSITION_ROOT_MANIFEST_NOT_PRIMARY` when present.

#### Forbidden promotions

- `lane_id=daemon_paper_24h` — forbidden
- `lane_id=remote_runtime` — forbidden
- `composition_index_authority=true` — forbidden
- Treating composition rollup manifest as lane primary evidence — forbidden
- Introducing `SHA256SUMS.stable.txt` as competing truth — forbidden (reuse `MANIFEST.sha256` only)

#### Illustrative anchor (non-authorizing)

- `RUN_ID=daemon_paper_24h_20260524T205447Z`
- Combined OUTROOT: `runs&#47;daemon_paper_24h&#47;{run_id}&#47;` with optional `manifests&#47;MANIFEST.sha256`
- Child lanes: `runs&#47;paper&#47;{run_id}&#47;`, `runs&#47;shadow&#47;{run_id}&#47;` — canonical per-lane evidence

## 7. Scheduler lane — launcher and CLI hard-block (partial verification)

```
SCHEDULER_BOUNDARY_LAUNCHER_GUARDED=true
P67_CLI_SCHEDULER_BOUNDARY_GUARDED=true
P67_LIBRARY_SCHEDULER_BOUNDARY_OPT_IN_IMPLEMENTED=true
SCHEDULER_LIBRARY_BYPASS_RESIDUAL=true
```

Normative state (post scheduler boundary hard-block #3584/#3585; library opt-in):

- `scripts/run_scheduler.py` non-dry-run entry is **hard-blocked** via shared `scripts/ops/scheduler_start_boundary_guard_v0.py` (`assert_scheduler_start_authorized()`).
- `src/ops/p67/shadow_session_scheduler_cli_v1.py` `main()` is **hard-blocked** by the same shared guard before `run_shadow_session_scheduler_v1()`.
- Direct library calls to `run_shadow_session_scheduler_v1()` (unit tests, P72 pack) **bypass** the CLI guard by default — residual risk; see [SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md](SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md) §7–§7b.
- Opt-in `scheduler_boundary_enforce=True` on `P67RunContextV1` / `P72PackContextV1` invokes the same shared guard at library entry; default off preserves unit tests and legacy library callers.

Normative rules:

- Scheduler diagnostics (`--dry-run --once`) are **planning_only**; they do not authorize daemon activation.
- Scheduler lane evidence **cannot infer** Live, Testnet, broker, or exchange authority.
- Explicit gate and operator approval remain required before any runtime scheduler execution.
- Hard-block semantics: [SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md](SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md).

## 7a. Scheduler completion evidence (opt-in)

```
SCHEDULER_COMPLETION_PRIMARY_EVIDENCE_CLOSEOUT_OPT_IN=true
PRIMARY_EVIDENCE_SHARED_HELPER_REUSED=true
```

Normative state (post scheduler completion closeout #3589):

- `scripts/run_scheduler.py` supports opt-in completion retention via `--evidence-dir` and `--primary-evidence-enforce` (default off).
- Writes `scheduler_completion_closeout_v0.json` when `--evidence-dir` is set.
- Calls shared `finalize_primary_evidence_root()` from `scripts/ops/primary_evidence_retention_v0.py` when enforcement is enabled.
- Does **not** alter scheduler start guard rules in §7; dry-run remains planning-only.
- Completion evidence remains **non-authorizing**; does not clear HOLD, preflight BLOCKED, or Live/Testnet/broker gates.

Detail owner: [SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md](SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md) §7a.

## 7b. Online readiness supervisor evidence pack (opt-in, offline)

```
SUPERVISOR_EVIDENCE_PACK_CLOSEOUT_OPT_IN=true
PRIMARY_EVIDENCE_SHARED_HELPER_REUSED=true
```

Normative state (post supervisor evidence pack closeout #3590):

- `scripts/ops/pack_online_readiness_supervisor_evidence_v0.py` is **operator-invoked after STOP** (offline; non-authorizing).
- Copies existing supervisor `OUT_DIR` into `{archive_root}&#47;supervisor_session&#47;` and optional pid/log artifacts into `{archive_root}&#47;supporting&#47;`.
- Writes `supervisor_session_closeout_v0.json`.
- Opt-in `--primary-evidence-enforce` calls shared `finalize_primary_evidence_root()`; archive root must be outside `/tmp` when enforce is set.
- Does **not** start/stop supervisor, online daemon, or invoke launchctl.
- Default supervisor/daemon driver pid/log paths may remain under `/tmp`; pack does not change driver defaults.

## 7c. Primary evidence closeout residual gaps

- In-process online daemon automatic session closeout pack is **not implemented**; operator must invoke post-stop wrapper (`run_online_readiness_post_stop_pack_v0.sh`) or pack script manually after STOP.
- Live-pilot / production retention hooks remain out of scope for this taxonomy index.
- Direct library calls to `run_shadow_session_scheduler_v1()` still bypass CLI scheduler guard (`SCHEDULER_LIBRARY_BYPASS_RESIDUAL=true`).
- Registry PASS, dashboard status, and readiness aggregate verdicts remain **non-authorizing**.

## 7d. P79 supervisor archive manifest gate (offline)

```
P79_SUPERVISOR_ARCHIVE_ROOT_MODE_IMPLEMENTED=true
P79_SUPERVISOR_PRIMARY_EVIDENCE_MANIFEST_VERIFY=true
P79_SUPERVISOR_RUNTIME_TICK_MODE_PRESERVED=true
P79_SUPERVISOR_GATE_NON_AUTHORIZING=true
PRIMARY_EVIDENCE_SHARED_HELPER_REUSED=true
```

Normative state (post P79 archive manifest gate #3592):

- `scripts/ops/p79_supervisor_health_gate_v1.sh` supports offline **ARCHIVE_ROOT** mode (mutually exclusive with runtime `OUT_DIR` tick mode).
- `scripts/ops/p79_supervisor_evidence_manifest_verify_v0.py` validates `supervisor_session_closeout_v0.json` and verifies `MANIFEST.sha256` via shared `verify_manifest_sha256()`.
- Consumes pack output from #3590; does **not** start/stop supervisor, online daemon, or invoke launchctl.
- Runtime tick/pidfile/P76 mode (including tick `manifest.json` one-of check) remains unchanged when `ARCHIVE_ROOT` is unset.
- P79 success is **non-authorizing**; does not clear HOLD, preflight BLOCKED, or Live/Testnet/broker/exchange gates.

Detail owner: [online_readiness_supervisor_health_gate_runbook_v1.md](../ai/online_readiness_supervisor_health_gate_runbook_v1.md).

## 7e. P101 post-stop primary evidence operator hints (non-executing)

```
P101_POST_STOP_PRIMARY_EVIDENCE_HINTS_IMPLEMENTED=true
P101_POST_STOP_PACK_HINT_REFERENCED=true
P101_POST_STOP_P79_ARCHIVE_VERIFY_HINT_REFERENCED=true
P101_POST_STOP_HINT_ONLY=true
P101_POST_STOP_PACK_NOT_EXECUTED=true
P101_POST_STOP_P79_VERIFY_NOT_EXECUTED=true
P101_POST_STOP_OPERATOR_EXPLICIT_REQUIRED=true
P101_POST_STOP_EVIDENCE_NON_AUTHORIZING=true
```

Normative state (post P101 post-stop operator hints #3595):

- `scripts/ops/p101_stop_playbook_v1.sh` emits a post-stop **hint block** to stdout and `P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt` after existing STOP semantics complete.
- Hints carry copy-paste examples for `run_online_readiness_post_stop_pack_v0.sh` (supervisor `OUT_DIR` → durable archive root; optional `--p79-archive-verify` for P79 **ARCHIVE_ROOT** offline manifest verification).
- P101 **does not** execute wrapper, pack, or P79 archive verification automatically; operator must run them explicitly after STOP.
- Hint semantics remain **non-authorizing**; do not clear HOLD, preflight BLOCKED, or Live/Testnet/broker/exchange gates.
- Post-stop wrapper hints for P91 audit snapshot runner: see §7i.

Detail owner: [p101_stop_playbook_v1.sh](../../../scripts/ops/p101_stop_playbook_v1.sh).

## 7f. Online readiness post-stop pack wrapper (operator-invoked, offline)

```
ONLINE_DAEMON_POST_STOP_PACK_WRAPPER_IMPLEMENTED=true
ONLINE_DAEMON_POST_STOP_WRAPPER_OPERATOR_INVOKED=true
ONLINE_DAEMON_POST_STOP_WRAPPER_NO_LAUNCHCTL=true
ONLINE_DAEMON_POST_STOP_WRAPPER_NON_AUTHORIZING=true
PRIMARY_EVIDENCE_SHARED_HELPER_REUSED=true
```

Normative state (post post-stop pack wrapper #3600/#3601/#3602):

- `scripts/ops/run_online_readiness_post_stop_pack_v0.sh` is the **canonical operator-invoked** post-stop path after daemon/supervisor STOP (offline; non-authorizing).
- Delegates to `pack_online_readiness_supervisor_evidence_v0.py`; does **not** duplicate pack or manifest verification logic.
- Optional `--p79-archive-verify` runs P79 **ARCHIVE_ROOT** gate only when explicitly set (off by default).
- Does **not** start/stop supervisor, online daemon, or invoke launchctl.
- P101/P93/P91 emit non-executing post-stop hints referencing this wrapper; hints do not auto-execute wrapper, pack, or P79.
- In-process online-daemon automatic pack remains **not implemented** (see §7c).

Detail owner: [run_online_readiness_post_stop_pack_v0.sh](../../../scripts/ops/run_online_readiness_post_stop_pack_v0.sh).

## 7g. P93 post-stop primary evidence operator hints (non-executing)

```
P93_POST_STOP_WRAPPER_HINTS_IMPLEMENTED=true
P93_POST_STOP_WRAPPER_REFERENCED=true
P93_POST_STOP_P79_ARCHIVE_VERIFY_HINT_REFERENCED=true
P93_POST_STOP_HINT_ONLY=true
P93_POST_STOP_WRAPPER_NOT_EXECUTED=true
P93_POST_STOP_PACK_NOT_EXECUTED=true
P93_POST_STOP_P79_VERIFY_NOT_EXECUTED=true
P93_POST_STOP_OPERATOR_EXPLICIT_REQUIRED=true
P93_POST_STOP_EVIDENCE_NON_AUTHORIZING=true
```

Normative state (post P93 post-stop operator hints #3599/#3601):

- `scripts/ops/p93_online_readiness_status_dashboard_v1.sh` emits a post-stop **hint block** to stdout and `P93_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt` after existing dashboard/status semantics complete.
- Hints carry copy-paste examples for `run_online_readiness_post_stop_pack_v0.sh` (supervisor `OUT_DIR` → durable archive root; optional `--p79-archive-verify` for P79 **ARCHIVE_ROOT** offline manifest verification).
- P93 **does not** execute wrapper, pack, or P79 archive verification automatically; operator must run them explicitly after STOP.
- Hint semantics remain **non-authorizing**; do not clear HOLD, preflight BLOCKED, or Live/Testnet/broker/exchange gates.
- Post-stop wrapper hints for P91 audit snapshot runner: see §7i.
- In-process online-daemon automatic pack remains **not implemented** (see §7c).

Detail owner: [p93_online_readiness_status_dashboard_v1.sh](../../../scripts/ops/p93_online_readiness_status_dashboard_v1.sh).

## 7i. P91 audit snapshot post-stop wrapper hints (non-executing)

```
P91_POST_STOP_WRAPPER_HINTS_IMPLEMENTED=true
P91_POST_STOP_WRAPPER_REFERENCED=true
P91_POST_STOP_P79_ARCHIVE_VERIFY_HINT_REFERENCED=true
P91_POST_STOP_HINT_ONLY=true
P91_POST_STOP_WRAPPER_NOT_EXECUTED=true
P91_POST_STOP_PACK_NOT_EXECUTED=true
P91_POST_STOP_P79_VERIFY_NOT_EXECUTED=true
P91_POST_STOP_OPERATOR_EXPLICIT_REQUIRED=true
P91_POST_STOP_EVIDENCE_NON_AUTHORIZING=true
```

Normative state (post P91 post-stop wrapper hint sync):

- `scripts/ops/p91_audit_snapshot_runner_v1.sh` emits a post-stop **hint block** to stdout and `P91_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt` after existing audit snapshot semantics complete.
- Hints carry copy-paste examples for `run_online_readiness_post_stop_pack_v0.sh` (supervisor `OUT_DIR` → durable archive root; optional `--p79-archive-verify` for P79 **ARCHIVE_ROOT** offline manifest verification).
- P91 **does not** execute wrapper, pack, or P79 **ARCHIVE_ROOT** archive verification automatically; operator must run them explicitly when durable §2a primary evidence is required.
- P91 remains **audit/snapshot hygiene** only — not a post-stop authority and not runtime authorization.
- Runtime P79 tick `manifest.json` under `OUT_DIR` is **not** equivalent to Preflight §2a `MANIFEST.sha256` verification.
- Hint semantics remain **non-authorizing**; do not clear HOLD, preflight BLOCKED, or Live/Testnet/broker/exchange gates.
- **No** launchctl/plist change in this slice; `p91_kickstart_when_ready_v1.sh` behavior unchanged.

Detail owner: [p91_audit_snapshot_runner_v1.sh](../../../scripts/ops/p91_audit_snapshot_runner_v1.sh).

## 7h. F5 read-only market dashboard (display, non-authorizing)

```
MARKET_DASHBOARD_READ_ONLY_NON_AUTHORITY=true
MARKET_DASHBOARD_NO_APPROVAL_AUTHORITY=true
MARKET_DASHBOARD_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true
```

Normative state (post Market Dashboard taxonomy cross-ref):

- F5 read-only market dashboard surfaces map to lane_id `dashboard` with authority level `review_input_only` (see §3).
- Detail owner: [FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) — futures-aware read-only display boundary (F5 stage).
- WebUI orientation surface [MARKET_SURFACE_V0.md](../../webui/MARKET_SURFACE_V0.md) remains orthogonal Kraken/OHLCV/dummy lineage; it does **not** replace the F5 contract owner.
- Dashboard display, SSR read models, registry rows, and test status **do not** grant approval, gate clearance, Live/Testnet/broker/exchange permission, scheduler activation, or runtime start.
- `FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL` applies (see §5).
- Master V2 / Double Play boundaries stay **protected**; dashboard must not reimplement selection or live decision authority (see §9).

## 8. Canary and Live-Canary lanes

- `canary` and `live_canary` governance docs are **not** Live authority.
- `canary_live_gate_v1` denies outbound Live/Canary paths (fail-closed).
- **Missing executable ops scripts** for Canary (`scripts&#47;ops&#47;*canary*`) does **not** imply permission; it means no authorized executable Canary ops path exists in-repo.
- `live_canary` (Canary Live per [CANARY_LIVE_ENTRY_CRITERIA.md](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md)) remains **separate from Testnet PASS**; Testnet success is never sufficient for Canary Live.

## 9. Master V2 / Double Play protection

```
MASTER_V2_DOUBLE_PLAY_BOUNDARY_PRESERVED=true
```

- Generic evidence lanes and readiness aggregates **cannot authorize** Master V2 / Double Play live execution.
- Master V2 / Double Play boundaries stay **protected**; this contract is **governance taxonomy only**.
- Display surfaces (dashboard, docs, AI orchestrator slices) must not reimplement Double Play selection or Master V2 decision authority.

## 10. Relation to Readiness Ledger, Mirror, and Gate Snapshot v0

```
READINESS_LEDGER_REVIEW_INPUT_ONLY=true
READINESS_MIRROR_NON_AUTHORIZING=true
GATE_SNAPSHOT_NO_APPROVAL_AUTHORITY=true
READINESS_AGGREGATE_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true
```

| Tool | Taxonomy role | Canonical owner |
|---|---|---|
| Readiness Evidence Ledger v0 | Triple-lane `paper` / `shadow` / `testnet` bounded evidence aggregate; `readiness_aggregate`; **review input only** | [build_readiness_evidence_ledger_v0.py](../../../scripts/ops/build_readiness_evidence_ledger_v0.py) |
| Readiness Ledger Preflight Mirror v0 | Consistency check between ledger and preflight; `review_input_only` | [report_readiness_ledger_preflight_mirror_v0.py](../../../scripts/ops/report_readiness_ledger_preflight_mirror_v0.py) |
| Readiness Gate Snapshot v0 | Non-authorizing composite of ledger + preflight + mirror (+ optional registry section); `readiness_aggregate` | [report_readiness_gate_snapshot_v0.py](../../../scripts/ops/report_readiness_gate_snapshot_v0.py) |

Normative state (readiness aggregate cross-ref):

- Readiness tooling produces **evidence/status/review inputs only**; it does **not** grant approval, gate clearance, Live/Testnet/broker/exchange permission, or trading authorization.
- Verdicts such as `READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE`, `READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE`, and `READINESS_GATE_SNAPSHOT_REVIEW_REQUIRED` remain **non-authorizing**; preflight **BLOCKED**, HOLD, and GLB blockers persist.
- Readiness outputs **do not** override scheduler boundary guards ([SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md](SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md)), preflight retention owners ([PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) §2a/§2b), or operator-explicit approval records.
- Ledger PASS for one bounded lane **does not** authorize another lane or Live paths (`FORBIDDEN_PROMOTION_*` in §5 apply).
- Preflight status remains canonical for scheduler start posture; mirror compares ledger vs preflight only — mirror PASS is not runtime authorization.

`GENERIC_EVIDENCE_REGISTRY_V1_IMPLEMENTED=true` — Registry v1 is implemented offline via `build_generic_evidence_run_registry_v1.py`; it remains **non-authorizing** and does not clear HOLD, preflight BLOCKED, or Live/Testnet/broker gates. Gate Snapshot may optionally include registry section; inclusion does not elevate authority.

### Bounded observation retention adapters (plan-only default, Stage-3 gated execute)

```
BOUNDED_OBSERVATION_ADAPTERS_TAXONOMY_INDEXED=true
BOUNDED_OBSERVATION_ADAPTERS_REVIEW_INPUT_ONLY=true
BOUNDED_OBSERVATION_ADAPTERS_STAGE3_EXECUTE_GATED=true
BOUNDED_OBSERVATION_ADAPTERS_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true
```

| Tool | Taxonomy role | Canonical owner |
|---|---|---|
| Paper bounded observation adapter v0 | Triple-lane `paper` bounded evidence retention; **plan-only default**; Stage-3 gated execute; **review input only** | [run_paper_only_bounded_observation_adapter_v0.py](../../../scripts/ops/run_paper_only_bounded_observation_adapter_v0.py) |
| Shadow bounded observation adapter v0 | Triple-lane `shadow` bounded evidence retention; **plan-only default**; Stage-3 gated execute; **review input only** | [run_shadow_bounded_observation_adapter_v0.py](../../../scripts/ops/run_shadow_bounded_observation_adapter_v0.py) |
| Testnet bounded observation adapter v0 | Triple-lane `testnet` bounded evidence retention; **plan-only default**; Stage-3 gated execute; **review input only** | [run_testnet_bounded_observation_adapter_v0.py](../../../scripts/ops/run_testnet_bounded_observation_adapter_v0.py) |

Normative state (bounded observation adapter cross-ref):

- Bounded observation adapters produce **command plans and bounded evidence/review inputs only** by default; they do **not** grant approval, gate clearance, Live/broker/exchange permission, or trading authorization.
- Default mode is **plan-only**; any `--execute` path requires explicit Stage-3 approval record and operator-explicit invocation — taxonomy indexing does **not** imply execute authority.
- Adapter outputs **do not** override scheduler boundary guards ([SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md](SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md)), preflight retention owners ([PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) §2a/§2b), operator-explicit approval records, or Master V2 / Double Play boundaries (`FORBIDDEN_PROMOTION_*` in §5 apply).
- Adapter PASS or durable archive copy for one bounded lane **does not** authorize another lane or Live paths.

#### Bounded observation evidence review scripts (offline, non-executing)

```
BOUNDED_OBSERVATION_REVIEW_SCRIPTS_TAXONOMY_INDEXED=true
BOUNDED_OBSERVATION_REVIEW_SCRIPTS_REVIEW_INPUT_ONLY=true
BOUNDED_OBSERVATION_REVIEW_SCRIPTS_NO_EXECUTE_AUTHORITY=true
BOUNDED_OBSERVATION_REVIEW_SCRIPTS_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true
```

| Tool | Taxonomy role | Canonical owner |
|---|---|---|
| Shadow bounded observation evidence review v0 | Offline review of shadow bounded observation archive evidence; **review input only**; does not execute adapters | [review_shadow_bounded_observation_evidence_v0.py](../../../scripts/ops/review_shadow_bounded_observation_evidence_v0.py) |
| Testnet bounded observation evidence review v0 | Offline review of testnet bounded observation archive evidence; **review input only**; does not execute adapters | [review_testnet_bounded_observation_evidence_v0.py](../../../scripts/ops/review_testnet_bounded_observation_evidence_v0.py) |

Normative state (bounded observation review script cross-ref):

- Review scripts inspect bounded observation evidence **after the fact**; they produce **review inputs only** and do **not** grant approval, gate clearance, Live/broker/exchange permission, adapter `--execute` authority, Stage-3 escalation, or runtime/scheduler start permission.
- Review PASS **does not** authorize adapter execution, another bounded lane, or Live paths (`FORBIDDEN_PROMOTION_*` in §5 apply).
- Review outputs **do not** override scheduler boundary guards, preflight retention owners, or operator-explicit approval records.

## 12. Autonomy stage authority crosswalk (normative index)

```
AUTONOMY_STAGE_AUTHORITY_CROSSWALK_V0=true
AUTONOMY_STAGE_COUNT=8
```

This section is the **normative crosswalk index** binding Master V2 **autonomy stages 0–7** (roadmap §3.1 vocabulary) to **max authority levels** (§4), **AI layer caps**, **evidence owners**, **required external/operator gates**, and **forbidden promotions** (§5). It does **not** authorize runtime, Live, Testnet execute, promotion, or model deployment.

**Reuse-before-new:** Stage names and informative posture remain owned by [MASTER_V2_GO_LIVE_ROADMAP_V0.md](MASTER_V2_GO_LIVE_ROADMAP_V0.md) §3.1. This section adds the **authority crosswalk only** — no parallel autonomy spec.

### 12.1 Authority inequality literals (always)

```
SIGNAL_NOT_TRADE=true
STRATEGY_NOT_AUTHORITY=true
AI_NOT_AUTHORITY=true
DASHBOARD_NOT_APPROVAL=true
EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true
TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true
KILLSWITCH_SAFETY_VETO_DOMINATES=true
AI_L6_EXEC_FORBIDDEN=true
GO_DECISION_REQUIRES_EXTERNAL_RECORD=true
```

- **KillSwitch / safety veto** dominates strategic switch-gate and advisory AI outputs ([MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)).
- **AI layer L6 EXEC** is **forbidden** ([AI_AUTONOMY_CONTROL_CENTER.md](../control_center/AI_AUTONOMY_CONTROL_CENTER.md)).
- **`go_decision_granted`** requires external human record (LB-APR-001 class per [CANARY_LIVE_ENTRY_CRITERIA.md](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md)); repo docs, evidence PASS, readiness aggregate, dashboard, Notion, and AI recommendations **cannot** substitute.

### 12.2 Normative crosswalk table (stages 0–7)

| stage | name (roadmap §3.1) | max authority level | AI layer cap | evidence owner (canonical) | required external/operator gate | forbidden promotion refs (§5) |
|---|---|---|---|---|---|---|
| `0` | Research / Backtest only | `planning_only` | L0–L2 (RO/REC) | offline research/backtest surfaces; `docs` lane | none for runtime | all Live/Testnet promotions |
| `1` | Shadow advisory | `evidence_only` / `review_input_only` | L0–L2 (RO/REC) | `shadow` bounded adapter + review scripts (§10) | Stage-3 if `--execute` | `FORBIDDEN_PROMOTION_SHADOW_TO_TESTNET_LIVE` |
| `2` | 24/7 Paper observation (distributed) | `evidence_only` | L0–L2 (RO/REC) | `paper` / `shadow` adapters; readiness aggregate (§10) | preflight **BLOCKED**; operator HOLD | `FORBIDDEN_PROMOTION_PAPER_TO_SHADOW_TESTNET_LIVE` |
| `3` | Paper autonomous candidate loop | `bounded_runtime_candidate` | L0–L3 (max PROP; **no L6 EXEC**) | `paper` adapter; preflight §2a retention | explicit Stage-3 approval + operator execute | `FORBIDDEN_PROMOTION_*`; scheduler hard-block (§7) |
| `4` | Testnet autonomous bounded loop | `scoped_runtime_exception` | L0–L3 (max PROP; **no L6 EXEC**) | `testnet` adapter + review scripts (§10) | Stage-3 approval; testnet-only charter | `FORBIDDEN_PROMOTION_TESTNET_PASS_TO_LIVE_BROKER_EXCHANGE` |
| `5` | Gated Live pilot | `live_authority_requires_separate_record` | L0–L4 (no L6 EXEC) | readiness ladder/index; GLB register; Canary criteria | external LB-APR-001 class + Canary manifest | `FORBIDDEN_PROMOTION_CANARY_DOCS_TO_LIVE`; GLB-014/015 |
| `6` | Bounded autonomous Live | `go_decision_granted` | L0–L4 (no L6 EXEC) | Canary manifest + session review surfaces | external Go within lease; KillSwitch path (GLB-008) | `FORBIDDEN_PROMOTION_GO_NO_GO_TEMPLATE_TO_GO_DECISION`; GLB-020 |
| `7` | Self-improving monitored autonomy | `operator_decision_required` | L0–L5 (L6 EXEC **forbidden**) | [MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md) **§10** approval SM; **§11** learning-change evidence pointer index; **§12** learning-trigger pointer index; AI evidence packs | approval state machine **§10**; evidence pointer index **§11** (non-authorizing); trigger pointer index **§12** (non-authorizing); online learning → live **prohibited** | `FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL` |

**Stage number ≠ authority level.** Higher automation surface does **not** imply higher repo authority without explicit external/operator gates.

### 12.3 Permanently operator-only or external-gated (never fully automated)

```
OPERATOR_ONLY_PERMANENT_GATES_DEFINED=true
```

The following remain **operator-only** or **external-gated** regardless of stage:

1. External Live/Canary **`go_decision_granted`** (LB-APR-001 class)
2. Canary manifest scope changes (exchange, symbol, strategy version, order types)
3. Capital ceiling / max-loss boundary increases (GLB-010/011)
4. KillSwitch arming/disarming **policy** changes (organizational; GLB-008)
5. GLB blocker acceptance/closure classification
6. Binding **`session_id`** selection for workflows claiming explicit session tie-in (GLB-006)
7. Promotion beyond bounded pilot (GLB-020)
8. Model/policy deployment to live path (approval chain partial — remains governed)
9. Scheduler **non-dry-run** authorization while hard-block active (§7)
10. Credential validity interpretation ([RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md](../runbooks/RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md))
11. Master V2 protected boundary changes (`MASTER_V2_DOUBLE_PLAY_BOUNDARY_PRESERVED=true`)

### 12.4 Non-goals (crosswalk)

- No new readiness/evidence/map/index/handoff/package surface
- No runtime, scheduler unlock, or Live/Testnet execute enablement
- No online learning activation path
- No duplicate autonomy taxonomy document

## 11. Revision

- **v0** — Initial lane taxonomy, authority levels, forbidden promotions, scheduler gap acknowledgment, Master V2 protection, registry field schema (deferred).
- **v0.1** — Truth-marker sync: registry v1 implemented; scheduler launcher + P67 CLI guarded; library bypass residual preserved.
- **v0.2** — Primary evidence closeout marker sync: scheduler completion (#3589) and supervisor offline pack (#3590) indexed as opt-in at canonical owners; default off; residual online-daemon/live-pilot gaps preserved.
- **v0.3** — P79 archive manifest gate marker sync (#3592): ARCHIVE_ROOT offline mode, shared manifest verify, runtime tick mode preserved, non-authorizing semantics indexed.
- **v0.4** — P101 post-stop operator hint marker sync (#3595/#3596): non-executing hint block for pack + P79 ARCHIVE_ROOT verify; operator-explicit; p93/p91 wiring gap preserved.
- **v0.5** — Post-stop pack wrapper cross-ref (#3600/#3601/#3602): operator-invoked wrapper indexed §7f; P101/P93 hints reference wrapper; in-process auto-pack deferred preserved.
- **v0.6** — P93 post-stop wrapper hint marker sync (#3599/#3601/#3603): dedicated §7g P93 hint markers; p91 wiring gap preserved.
- **v0.7** — P67/P72 library scheduler boundary opt-in: `scheduler_boundary_enforce` default off; shared guard at library entry; `SCHEDULER_LIBRARY_BYPASS_RESIDUAL` preserved.
- **v0.8** — F5 read-only market dashboard taxonomy cross-ref: §7h markers; `dashboard` lane `review_input_only`; F5 contract owner indexed.
- **v0.9** — Readiness aggregate cross-ref: §10 markers and script owners for ledger/mirror/gate snapshot; non-authorizing review-input-only semantics strengthened.
- **v1.0** — Bounded observation adapter cross-ref: §10 subsection indexes paper/shadow/testnet retention adapters; plan-only default; Stage-3 gated execute; review-input-only semantics.
- **v1.1** — Bounded observation review script cross-ref: §10 indexes shadow/testnet evidence review scripts; offline; non-executing; review-input-only semantics.
- **v1.2** — Autonomy stage authority crosswalk §12: stages 0–7 → max authority, AI layer caps, evidence owners, external/operator gates, forbidden promotions; reuse roadmap §3.1 vocabulary; no parallel autonomy spec.
- **v1.3** — Inventory §11 learning-change evidence index cross-ref: §12.2 stage-7 row and owner table index **§11** pointer index alongside **§10** approval SM; pointer-only; non-authorizing.
- **v1.4** — Inventory §12 learning-trigger pointer index cross-ref: §12.2 stage-7 row and owner table index **§12** (Inventory §12) alongside **§10**/**§11**; distinct from this spec §12 autonomy crosswalk; pointer-only; non-authorizing.
