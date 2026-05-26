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
POST_CLOSEOUT_PROJECTION_AUTOMATION_V0=true
NOTION_POST_CLOSEOUT_SYNC_V0=true
MARKET_DASHBOARD_READONLY_RUN_PROJECTION_V0=true
POST_CLOSEOUT_PROJECTION_AUTOMATION_ENABLED=false
NOTION_POST_CLOSEOUT_SYNC_ENABLED=false
MARKET_DASHBOARD_RUN_PROJECTION_ENABLED=false
RUNTIME_CONTROL_FROM_PROJECTION=false
DASHBOARD_RUNTIME_CONTROL=false
BROKER_EXCHANGE_AUTHORITY=false
PROJECTION_AFTER_CLOSEOUT_ONLY=true
PROJECTION_AFTER_MANIFEST_VERIFY_ONLY=true
REPO_AND_DURABLE_EVIDENCE_REMAIN_CANONICAL=true
NOTION_IS_PROJECTION_ONLY=true
MARKET_DASHBOARD_IS_PROJECTION_ONLY=true
NO_PARALLEL_MARKET_SURFACE=true
NO_PARALLEL_NOTION_DB=true
NO_PARALLEL_READMODEL=true
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
REMOTE_RUNTIME_COMMAND_CONTRACT_V0=true
REMOTE_RUNTIME_COMMAND_CONTRACT_DOCS_TESTS_ONLY=true
REMOTE_RUNTIME_RUNNER_PREFLIGHT_V0=true
REMOTE_RUNTIME_RUNNER_PREFLIGHT_DOCS_TESTS_ONLY=true
REMOTE_PAPER_APPROVAL_COMMAND_PACKET_CONTRACT_V0=true
REMOTE_PAPER_APPROVAL_COMMAND_PACKET_DOCS_TESTS_ONLY=true
REMOTE_HOST_INVENTORY_PLANNING_CONTRACT_V0=true
REMOTE_HOST_INVENTORY_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true
REMOTE_COST_KILL_ORPHAN_SAFETY_CONTRACT_V0=true
REMOTE_COST_KILL_ORPHAN_SAFETY_CONTRACT_DOCS_TESTS_ONLY=true
REMOTE_PAPER_PACKET_ASSEMBLY_VALIDATOR_PLANNING_CONTRACT_V0=true
REMOTE_PAPER_PACKET_ASSEMBLY_VALIDATOR_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true
REMOTE_PAPER_VALIDATOR_CLI_PLANNING_CONTRACT_V0=true
REMOTE_PAPER_VALIDATOR_CLI_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true
REMOTE_PAPER_DRY_COMMAND_TEMPLATE_PLANNING_CONTRACT_V0=true
REMOTE_PAPER_DRY_COMMAND_TEMPLATE_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true
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
| §2b.1 mandatory durable closeout | [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) §2b.1 |
| §2b.2 closeout enforcement planning | [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) §2b.2 |
| §6a.0.7 remote paper dry command template planning | This spec §6a.0.7 (planning-only; non-executable) |
| §6a.0.8 post-closeout projection automation charter | This spec §6a.0.8 (docs/tests-only; binds §6a.1 / §6a.2 / Registry v1) |
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

**Rule:** This spec is the **lane ID and authority-level index** (including §12 autonomy-stage crosswalk). Retention rules remain in preflight §2a/§2b/§2b.1. Stage vocabulary owner remains roadmap §3.1 — **do not renumber** stages here.

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
- **merge_closeout** — §2b.1 mandatory durable merge/post-PR closeouts under `{archive}&#47;closeout&#47;` (or `planning&#47;` when §2b applies)
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

### 6a.0 Remote Runtime Command Contract v0 (paper-only command shape, non-executing)

```
REMOTE_RUNTIME_COMMAND_CONTRACT_V0=true
REMOTE_RUNTIME_COMMAND_CONTRACT_DOCS_TESTS_ONLY=true
REMOTE_RUNTIME_IS_BACKEND_NOT_LANE=true
LANE_ID_REMOTE_RUNTIME_FORBIDDEN=true
REMOTE_RUNTIME_V0_PAPER_ONLY=true
REMOTE_RUNTIME_V0_TESTNET_AUTHORITY=false
REMOTE_RUNTIME_V0_LIVE_AUTHORITY=false
REMOTE_RUNTIME_V0_BROKER_CREDENTIALS_FORBIDDEN=true
REMOTE_RUNTIME_V0_REQUIRES_MAX_RUNTIME_SECONDS=true
REMOTE_RUNTIME_V0_REQUIRES_REMOTE_RUN_ID=true
REMOTE_RUNTIME_V0_REQUIRES_REMOTE_DURABLE_EVIDENCE_ROOT=true
REMOTE_RUNTIME_V0_REQUIRES_MANIFEST_SHA256=true
REMOTE_RUNTIME_V0_REQUIRES_MANIFEST_VERIFY_RC_ZERO=true
REMOTE_RUNTIME_V0_REQUIRES_MANDATORY_DURABLE_CLOSEOUT=true
REMOTE_RUNTIME_V0_REUSES_SCHEDULER_BOUNDARY_GUARD=true
REMOTE_RUNTIME_V0_REUSES_HOLD_BINDING=true
REMOTE_RUNTIME_V0_REUSES_REGISTRY_V1=true
REMOTE_RUNTIME_V0_S3_AFTER_FINALIZE_ONLY=true
REMOTE_RUNTIME_V0_NOTION_PROJECTION_ONLY=true
REMOTE_RUNTIME_V0_MARKET_DASHBOARD_PROJECTION_ONLY=true
REMOTE_RUNTIME_V0_NO_REMOTE_RUNNER_IMPLEMENTATION=true
REMOTE_RUNTIME_V0_NO_AWS_RCLONE_NETWORK_EXECUTION=true
TMP_ONLY_EVIDENCE_INVALID=true
EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true
```

**Purpose:** Define the **normative command / metadata / gate shape** for future laptop-independent **remote Paper-only** execution — **without** implementing a remote runner, AWS host, systemd unit, GHA runner, SSH command, network action, or scheduler start in this slice.

**Normative rule:** Remote Runtime remains **backend metadata** for existing bounded lanes (§6a above). This contract describes the **future command contract fields and gate chain** only; it **does not** execute, deploy, or authorize runtime.

#### Allowed v0 lane and forbidden surfaces

| Surface | v0 posture |
|---|---|
| `lane_id=paper` | **Only** allowed bounded lane for first remote runtime command contract |
| `lane_id=shadow` | **Forbidden by default** in v0 remote command contract (defer to later stage) |
| `lane_id=testnet` | **Forbidden** — `REMOTE_RUNTIME_V0_TESTNET_AUTHORITY=false` |
| `lane_id=remote_runtime` | **Forbidden** — `LANE_ID_REMOTE_RUNTIME_FORBIDDEN=true` |
| `lane_id=daemon_paper_24h` | **Forbidden as lane** — composition wrapper only (§6b); not a runtime lane |
| Live / broker / exchange | **Forbidden** — `REMOTE_RUNTIME_V0_LIVE_AUTHORITY=false`; `REMOTE_RUNTIME_V0_BROKER_CREDENTIALS_FORBIDDEN=true` |
| AWS / rclone / S3 upload / network | **Forbidden in command contract** — `REMOTE_RUNTIME_V0_NO_AWS_RCLONE_NETWORK_EXECUTION=true` |

#### Required command / metadata fields (future remote paper-only)

These fields document the **future non-executing command contract shape** for operator planning and Registry v1 row metadata. They **do not** authorize runtime when present alone.

| Field | Required (v0) | Allowed values (v0) |
|---|---|---|
| `lane_id` | yes | `paper` only |
| `runtime_host` | yes | `remote` |
| `runtime_backend` | yes | `ec2` \| `vps` \| `gha_runner` \| `data_node` |
| `runtime_mode` | yes | `paper_only` |
| `remote_run_id` | yes | opaque run identifier (same semantics as bounded `run_id`) |
| `max_runtime_seconds` | yes | positive bounded wall-clock cap |
| `evidence_root_type` | yes | `remote_durable` |
| `evidence_transport` | yes | `local_only` \| `s3_export_after_finalize` (planning metadata only until finalize) |
| `live_authority` | yes | `false` only |
| `testnet_authority` | yes | `false` only |

When `evidence_transport=s3_export_after_finalize` appears in planning metadata, operators must use [preflight_s3_finalized_evidence_export_v0.py](../../../scripts/ops/preflight_s3_finalized_evidence_export_v0.py) with `--export-prefix-plan` **after** finalize — prefix-plan is **non-executing**; upload does **not** authorize runtime (§6a.3).

#### Required gate chain (all must hold before any future remote paper execution)

Future remote paper execution **must reuse** the same canonical gate chain as local bounded runs — **no bypass**, **no parallel scheduler authority**:

1. [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) — preflight posture (default **BLOCKED** unchanged by this contract).
2. [SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md](SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md) + [scheduler_start_boundary_guard_v0.py](../../../scripts/ops/scheduler_start_boundary_guard_v0.py) — `REMOTE_RUNTIME_V0_REUSES_SCHEDULER_BOUNDARY_GUARD=true`.
3. [paper_shadow_247_scheduler_hold_runtime_binding_v0.py](../../../scripts/ops/paper_shadow_247_scheduler_hold_runtime_binding_v0.py) — RUN_ID-scoped HOLD binding when scheduler subprocess is in scope — `REMOTE_RUNTIME_V0_REUSES_HOLD_BINDING=true`.
4. Bounded adapter approval record — same Stage-3 executing approval chain as local paper bounded observation (reuse [run_paper_only_bounded_observation_adapter_v0.py](../../../scripts/ops/run_paper_only_bounded_observation_adapter_v0.py); no new approval surface).
5. Preflight §2a / §2a.1 primary evidence — [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py); durable root outside `/tmp`; `MANIFEST.sha256` RC=0.
6. Preflight §2b.1 mandatory durable closeout — material closeout complete on durable archive; `/tmp`-only remote evidence **`TMP_ONLY_EVIDENCE_INVALID`**.
7. [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) — Registry v1 metadata row with §6a fields — `REMOTE_RUNTIME_V0_REUSES_REGISTRY_V1=true`.
8. Local S3 preflight + prefix-plan — **only if** S3 transport is planned post-finalize (§6a.3 / §6a.3.1); dry-run only in v0.

#### Required output / evidence semantics (remote durable root)

All of the following are **required** before treating a remote paper run as complete:

- Durable evidence root **outside `/tmp`** on the remote host (`REMOTE_RUNTIME_V0_REQUIRES_REMOTE_DURABLE_EVIDENCE_ROOT=true`).
- `MANIFEST.sha256` present (`REMOTE_RUNTIME_V0_REQUIRES_MANIFEST_SHA256=true`).
- Manifest verify **RC=0** (`REMOTE_RUNTIME_V0_REQUIRES_MANIFEST_VERIFY_RC_ZERO=true`).
- Closeout marker present per §2a.1 (shared helper `KNOWN_CLOSEOUT_FILENAMES` / review closeout semantics).
- Material closeout §2b.1 complete when used as merge/operator evidence (`REMOTE_RUNTIME_V0_REQUIRES_MANDATORY_DURABLE_CLOSEOUT=true`).
- `/tmp`-only remote artifacts remain **invalid** regardless of exit code.

Remote host placement **does not** relax manifest, closeout, or preflight rules.

#### Forbidden parallel builds (normative)

- Second scheduler authority — forbidden; reuse §7 shared guard only.
- Second evidence root standard — forbidden; `MANIFEST.sha256` via `primary_evidence_retention_v0.py` only.
- Second closeout index standard — forbidden; §2b.1 durable archive owner remains canonical.
- S3 as runtime or approval — forbidden; `S3_AUTHORITY=false` (§6a.3).
- Notion as source of truth — forbidden; Registry v1 sole feed (§6a.1); `REMOTE_RUNTIME_V0_NOTION_PROJECTION_ONLY=true`.
- Dashboard as runtime / testnet / live authority — forbidden (§6a.2); `REMOTE_RUNTIME_V0_MARKET_DASHBOARD_PROJECTION_ONLY=true`.
- Remote host with live/testnet credentials in v0 — forbidden.
- Remote runner bypassing existing gates — forbidden.

#### Notion and Market Dashboard (projection-only in this contract)

- Notion: §6a.1 — post-closeout sync only; `NOTION_WRITE_DEFAULT=false`; no writes in this contract slice.
- Market Dashboard: §6a.2 — read-only Registry v1 projection; no runtime actions; `GET &#47;market&#47;double-play` untouched.

#### S3 (after-finalize-only)

```
REMOTE_RUNTIME_V0_S3_AFTER_FINALIZE_ONLY=true
S3_UPLOAD_BEFORE_FINALIZE_FORBIDDEN=true
DOWNLOAD_VERIFY_REQUIRED_BEFORE_CLOSEOUT_ACCEPTANCE=true
```

- Export prefix-plan from `preflight_s3_finalized_evidence_export_v0.py` is **planning-only** and **non-executing**.
- Upload success does **not** authorize runtime or closeout acceptance.
- Consumer download + `MANIFEST.sha256` verify RC=0 required before accepting remote object copies (§6a.3).

#### Implementation posture (this slice)

```
REMOTE_RUNTIME_V0_NO_REMOTE_RUNNER_IMPLEMENTATION=true
REMOTE_RUNTIME_V0_NO_AWS_RCLONE_NETWORK_EXECUTION=true
```

This contract is **static / normative only** (`REMOTE_RUNTIME_COMMAND_CONTRACT_DOCS_TESTS_ONLY=true`). It **does not** ship an execution script, remote command implementation, AWS/GHA/systemd/SSH wiring, or scheduler start path.

Cross-reference: [REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md](REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md) Class A scheduled evidence before Class B daemon; composition-index §6b for deferred `paper_then_shadow`.

#### 6a.0.1 Local remote runner preflight v0 (non-executing CLI)

```
REMOTE_RUNTIME_RUNNER_PREFLIGHT_V0=true
REMOTE_RUNTIME_RUNNER_PREFLIGHT_DOCS_TESTS_ONLY=true
REMOTE_RUNTIME_RUNNER_PREFLIGHT_DRY_RUN_REQUIRED=true
REMOTE_RUNTIME_RUNNER_PREFLIGHT_NO_NETWORK_REQUIRED=true
REMOTE_RUNTIME_V0_NO_REMOTE_RUNNER_IMPLEMENTATION=true
RUNNER_IMPLEMENTED=false
```

**Purpose:** Provide a **local-only, non-executing** preflight that validates whether a future remote **Paper-only** runner command shape would satisfy §6a.0 **before** any real remote runner, AWS host, GHA runner, SSH, systemd, or scheduler implementation exists.

**Implementation owner:** [preflight_remote_runtime_runner_v0.py](../../../scripts/ops/preflight_remote_runtime_runner_v0.py) — dry-run CLI only; emits JSON eligibility checklist; **does not** start runners, schedulers, daemons, or network actions.

**Required CLI flags (v0):** `--dry-run`, `--no-network`, `--runtime-host remote`, `--runtime-backend`, `--runtime-mode paper_only`, `--lane-id paper`, `--remote-run-id`, `--max-runtime-seconds`, `--evidence-root-type remote_durable`, `--evidence-transport` ∈ {`local_only`, `s3_export_after_finalize_plan`}, optional `--out`, `--registry-json`, `--s3-prefix-plan-json`, `--approval-record`, `--scheduler-guard-json`.

**Fail-closed:** Missing `--dry-run` or `--no-network`; any forbidden lane (`remote_runtime`, `daemon_paper_24h`, `shadow`, `testnet`, `live`); non-`paper_only` mode; non-`remote` host; invalid backend; unsafe `max_runtime_seconds`; registry conflicts; non-executing S3 prefix-plan mismatches; forbidden approval/guard markers implying live/testnet/broker/network/AWS execution.

**Output:** JSON with `status` ∈ {`eligible`, `blocked`, `invalid`} and non-authority boundary fields (`runner_implemented=false`, `network_called=false`, etc.). Preflight **does not** authorize runtime, clear HOLD, or grant gates.

#### 6a.0.2 Remote paper approval/command packet contract v0 (non-executable)

```
REMOTE_PAPER_APPROVAL_COMMAND_PACKET_CONTRACT_V0=true
REMOTE_PAPER_APPROVAL_COMMAND_PACKET_DOCS_TESTS_ONLY=true
REMOTE_PAPER_PACKET_NON_EXECUTABLE=true
REMOTE_PAPER_PACKET_DO_NOT_RUN=true
REMOTE_PAPER_PACKET_RUNNER_IMPLEMENTED=false
REMOTE_PAPER_PACKET_APPROVE_REMOTE_RUNNER_START_NOW=false
REMOTE_PAPER_PACKET_LANE_ID_REQUIRED=paper
REMOTE_PAPER_PACKET_REMOTE_RUNTIME_BACKEND_NOT_LANE=true
REMOTE_PAPER_PACKET_LANE_ID_REMOTE_RUNTIME_FORBIDDEN=true
REMOTE_PAPER_PACKET_LANE_ID_DAEMON_PAPER_24H_NOT_LANE=true
REMOTE_PAPER_PACKET_SHADOW_DEFAULT_FORBIDDEN=true
REMOTE_PAPER_PACKET_TESTNET_FORBIDDEN=true
REMOTE_PAPER_PACKET_LIVE_FORBIDDEN=true
REMOTE_PAPER_PACKET_BROKER_CREDENTIALS_FORBIDDEN=true
REMOTE_PAPER_PACKET_AWS_RCLONE_NETWORK_EXECUTION_FORBIDDEN=true
REMOTE_PAPER_PACKET_SSH_SYSTEMD_GHA_RUNNER_FORBIDDEN=true
REMOTE_PAPER_PACKET_REQUIRES_PREFLIGHT_JSON=true
REMOTE_PAPER_PACKET_REQUIRES_SCHEDULER_GUARD=true
REMOTE_PAPER_PACKET_REQUIRES_HOLD_BINDING=true
REMOTE_PAPER_PACKET_REQUIRES_BOUNDED_ADAPTER_APPROVAL=true
REMOTE_PAPER_PACKET_REQUIRES_REGISTRY_V1=true
REMOTE_PAPER_PACKET_REQUIRES_PRIMARY_EVIDENCE_RETENTION=true
REMOTE_PAPER_PACKET_REQUIRES_MANDATORY_DURABLE_CLOSEOUT=true
REMOTE_PAPER_PACKET_S3_PREFIX_PLAN_OPTIONAL_NON_EXECUTING=true
REMOTE_PAPER_PACKET_NOTION_PROJECTION_ONLY=true
REMOTE_PAPER_PACKET_MARKET_DASHBOARD_PROJECTION_ONLY=true
REMOTE_PAPER_PACKET_READY_FOR_START=false
REMOTE_PAPER_PACKET_OPERATOR_APPROVAL_REQUIRED=true
REMOTE_PAPER_PACKET_NOT_NEW_APPROVAL_AUTHORITY=true
```

**Purpose:** Define a **non-executable** operator approval/command **packet** that binds together all §6a.0 gate inputs **before** any future Remote Paper-only runner **implementation review** or **start** can be considered — **without** shipping a runner, dry command template, AWS/EC2/GHA/systemd/SSH wiring, scheduler start, runtime start, broker/exchange access, S3 upload/download, or Notion/Dashboard writes.

**Normative rule:** This packet **extends** the existing bounded adapter approval / operator decision chain (§6a.0 gate item 4). It is **not** a new approval authority and **does not** replace scheduler boundary guard, HOLD binding, Registry v1, Preflight §2a/§2a.1, or §2b.1 mandatory durable closeout.

**Fixture owner (non-authorizing):** [remote_paper_approval_command_packet_v0.json](../../../tests/fixtures/ops/remote_paper_approval_command_packet_v0.json) — example packet shape only; `DO_NOT_RUN=true`; **does not** authorize execution.

#### Required packet identity fields (v0)

| Field | Required value / rule |
|---|---|
| `remote_run_id` | Non-empty; safe run id |
| `runtime_host` | `remote` |
| `runtime_backend` | `ec2` \| `vps` \| `gha_runner` \| `data_node` |
| `runtime_mode` | `paper_only` |
| `lane_id` | `paper` only (`REMOTE_PAPER_PACKET_LANE_ID_REQUIRED=paper`) |
| `max_runtime_seconds` | Positive bounded cap |
| `evidence_root_type` | `remote_durable` |
| `evidence_transport` | `local_only` or `s3_export_after_finalize_plan` |

#### Required packet input pointers (hashes or durable paths)

All pointers are **non-authorizing references** to artifacts that must exist and verify before packet status may be `prepared_not_executable`:

1. **Preflight JSON** — output from [preflight_remote_runtime_runner_v0.py](../../../scripts/ops/preflight_remote_runtime_runner_v0.py) with `status=eligible` (`REMOTE_PAPER_PACKET_REQUIRES_PREFLIGHT_JSON=true`).
2. **Scheduler guard snapshot** — [scheduler_start_boundary_guard_v0.py](../../../scripts/ops/scheduler_start_boundary_guard_v0.py) JSON (`REMOTE_PAPER_PACKET_REQUIRES_SCHEDULER_GUARD=true`).
3. **HOLD binding** — [paper_shadow_247_scheduler_hold_runtime_binding_v0.py](../../../scripts/ops/paper_shadow_247_scheduler_hold_runtime_binding_v0.py) RUN_ID-scoped binding when scheduler subprocess is in scope (`REMOTE_PAPER_PACKET_REQUIRES_HOLD_BINDING=true`).
4. **Bounded adapter approval record** — reuse Stage-3 paper bounded observation approval chain ([run_paper_only_bounded_observation_adapter_v0.py](../../../scripts/ops/run_paper_only_bounded_observation_adapter_v0.py); no parallel approval surface) (`REMOTE_PAPER_PACKET_REQUIRES_BOUNDED_ADAPTER_APPROVAL=true`).
5. **Registry v1 row** — [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) `runs[]` metadata with §6a fields (`REMOTE_PAPER_PACKET_REQUIRES_REGISTRY_V1=true`).
6. **Primary evidence retention** — Preflight §2a / §2a.1 + [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) contract pointer (`REMOTE_PAPER_PACKET_REQUIRES_PRIMARY_EVIDENCE_RETENTION=true`).
7. **Mandatory durable closeout** — Preflight §2b.1 contract pointer (`REMOTE_PAPER_PACKET_REQUIRES_MANDATORY_DURABLE_CLOSEOUT=true`).
8. **S3 export prefix-plan (optional)** — [preflight_s3_finalized_evidence_export_v0.py](../../../scripts/ops/preflight_s3_finalized_evidence_export_v0.py) `--export-prefix-plan` JSON **only when** `evidence_transport=s3_export_after_finalize_plan`; non-executing; upload does **not** authorize runtime (`REMOTE_PAPER_PACKET_S3_PREFIX_PLAN_OPTIONAL_NON_EXECUTING=true`).

#### Forbidden packet semantics (fail-closed)

| Forbidden | Marker |
|---|---|
| `lane_id=remote_runtime` | `REMOTE_PAPER_PACKET_LANE_ID_REMOTE_RUNTIME_FORBIDDEN=true` |
| `lane_id=daemon_paper_24h` as runtime lane | `REMOTE_PAPER_PACKET_LANE_ID_DAEMON_PAPER_24H_NOT_LANE=true` |
| Shadow default / shadow lane authority | `REMOTE_PAPER_PACKET_SHADOW_DEFAULT_FORBIDDEN=true` |
| Testnet | `REMOTE_PAPER_PACKET_TESTNET_FORBIDDEN=true` |
| Live / broker / exchange | `REMOTE_PAPER_PACKET_LIVE_FORBIDDEN=true`; `REMOTE_PAPER_PACKET_BROKER_CREDENTIALS_FORBIDDEN=true` |
| AWS / rclone / network execution | `REMOTE_PAPER_PACKET_AWS_RCLONE_NETWORK_EXECUTION_FORBIDDEN=true` |
| SSH / systemd / GHA runner wiring | `REMOTE_PAPER_PACKET_SSH_SYSTEMD_GHA_RUNNER_FORBIDDEN=true` |
| Executable command template in packet | forbidden — `REMOTE_PAPER_PACKET_NON_EXECUTABLE=true` |
| Runner implementation implied | forbidden — `REMOTE_PAPER_PACKET_RUNNER_IMPLEMENTED=false` |

#### Required packet output / final machine lines

Future operator tooling may emit a packet summary JSON or markdown footer with:

| Line | Allowed values |
|---|---|
| `REMOTE_PAPER_PACKET_STATUS` | `prepared_not_executable` \| `blocked` \| `invalid` |
| `REMOTE_PAPER_PACKET_READY_FOR_IMPLEMENTATION_REVIEW` | `true` \| `false` (review-only; **not** start authority) |
| `REMOTE_PAPER_PACKET_READY_FOR_START` | **`false` always in v0** |
| `REMOTE_PAPER_PACKET_OPERATOR_APPROVAL_REQUIRED` | **`true` always in v0** |
| `REMOTE_PAPER_PACKET_RUNTIME_COMMANDS_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_AWS_CLI_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_NETWORK_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_SSH_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_SYSTEMD_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_S3_UPLOAD_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_S3_DOWNLOAD_CALLED` | **`false`** |

`prepared_not_executable` means all input pointers verify and §6a.0.1 preflight would be `eligible` — it **still does not** authorize runner implementation, scheduler start, or runtime start.

#### Notion and Market Dashboard (projection-only)

- `REMOTE_PAPER_PACKET_NOTION_PROJECTION_ONLY=true` — future Notion may display packet status from Registry/projection only; no approval/start authority (§6a.1).
- `REMOTE_PAPER_PACKET_MARKET_DASHBOARD_PROJECTION_ONLY=true` — future Dashboard may display packet status read-only; no runtime actions (§6a.2).

#### S3 (optional prefix-plan pointer only)

- Prefix-plan pointer required only when S3 transport is planned post-finalize.
- Upload does **not** authorize runtime or closeout acceptance (§6a.3).
- Consumer download + `MANIFEST.sha256` verify RC=0 required before accepting remote object copies.

#### Implementation posture (this slice)

This contract is **static / normative only** (`REMOTE_PAPER_APPROVAL_COMMAND_PACKET_DOCS_TESTS_ONLY=true`). It **does not** ship packet assembly CLI, runner implementation, dry command template, AWS/GHA/systemd/SSH wiring, or scheduler start path.

Cross-reference: §6a.0 command shape; §6a.0.1 local preflight; §6a.3/§6a.3.1 S3 after-finalize; Preflight §2a/§2b.1; composition-index §6b (orthogonal; `daemon_paper_24h` is not a runtime lane).

#### 6a.0.3 Remote host inventory planning contract v0 (planning-only)

```
REMOTE_HOST_INVENTORY_PLANNING_CONTRACT_V0=true
REMOTE_HOST_INVENTORY_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true
REMOTE_HOST_INVENTORY_PLANNING_ONLY=true
REMOTE_HOST_INVENTORY_DO_NOT_PROVISION=true
REMOTE_HOST_INVENTORY_DO_NOT_CONNECT=true
REMOTE_HOST_INVENTORY_NO_AWS_CLI=true
REMOTE_HOST_INVENTORY_NO_SSH=true
REMOTE_HOST_INVENTORY_NO_SYSTEMD=true
REMOTE_HOST_INVENTORY_NO_GHA_RUNNER=true
REMOTE_HOST_INVENTORY_NO_NETWORK=true
REMOTE_HOST_INVENTORY_NOT_APPROVAL=true
REMOTE_HOST_INVENTORY_NOT_RUNTIME_START=true
REMOTE_HOST_INVENTORY_NOT_CREDENTIAL_GRANT=true
REMOTE_HOST_INVENTORY_NOT_TESTNET_OR_LIVE_GATE=true
REMOTE_HOST_INVENTORY_REQUIRES_REMOTE_DURABLE_ROOT_CONVENTION=true
REMOTE_HOST_INVENTORY_REQUIRES_COST_CEILING=true
REMOTE_HOST_INVENTORY_REQUIRES_STOP_PROCEDURE=true
REMOTE_HOST_INVENTORY_REQUIRES_ORPHAN_DETECTION=true
REMOTE_HOST_INVENTORY_REQUIRES_TEARDOWN_OWNER=true
REMOTE_HOST_INVENTORY_FORBIDS_REAL_IPS=true
REMOTE_HOST_INVENTORY_FORBIDS_CREDENTIALS=true
REMOTE_HOST_INVENTORY_FORBIDS_ACCOUNT_IDS=true
REMOTE_HOST_INVENTORY_FORBIDS_PROVIDER_INSTANCE_IDS=true
REMOTE_HOST_INVENTORY_FORBIDS_SSH_USERNAMES_KEYS=true
REMOTE_HOST_INVENTORY_FORBIDS_REAL_BUCKET_NAMES=true
REMOTE_HOST_INVENTORY_PAPER_ONLY=true
REMOTE_HOST_INVENTORY_LIVE_AUTHORITY=false
REMOTE_HOST_INVENTORY_TESTNET_AUTHORITY=false
```

**Purpose:** Define **non-authorizing** remote host inventory fields and ownership boundaries required **before** any future Remote Paper-only **implementation charter** can be considered — **without** provisioning, inspecting, connecting to, or managing any host, cloud account, network endpoint, or credential store.

**Normative rule:** Inventory rows are **planning metadata only** (`REMOTE_HOST_INVENTORY_PLANNING_ONLY=true`). They **extend** §6a host metadata and bind to §6a.0 / §6a.0.1 / §6a.0.2 — they **do not** approve runtime, grant credentials, clear Preflight **BLOCKED**, or substitute for bounded adapter approval.

**Fixture owner (non-authorizing):** [remote_host_inventory_planning_v0.json](../../../tests/fixtures/ops/remote_host_inventory_planning_v0.json) — fake planning-only example; **does not** describe a live resource.

#### Required inventory fields (v0)

| Field | Required value / rule |
|---|---|
| `remote_host_id` | Planning-only synthetic id (e.g. `planning_host_<slug>`); **not** a cloud provider instance id |
| `runtime_backend` | `ec2` \| `vps` \| `gha_runner` \| `data_node` |
| `host_owner` | Named operator/team responsible for host lifecycle planning |
| `operator_owner` | Named operator responsible for run/evidence planning |
| `environment_class` | **`planning_only`** only in v0 |
| `remote_durable_root_convention` | Path convention outside `/tmp` on remote host (template, not live path) |
| `log_root_convention` | Non-authorizing log path convention |
| `closeout_root_convention` | Aligns with Preflight §2b.1 durable closeout owner pattern |
| `registry_v1_pointer` | Pointer to Registry v1 row / builder contract |
| `credential_boundary` | Pointer to [RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md](../runbooks/RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md) |
| `secrets_present` | **`false`** in v0 planning rows |
| `broker_credentials_present` | **`false`** |
| `exchange_credentials_present` | **`false`** |
| `live_authority` | **`false`** |
| `testnet_authority` | **`false`** |
| `paper_only` | **`true`** |
| `max_instance_lifetime_required` | **`true`** — bounded lifetime must be declared before charter |
| `max_runtime_seconds_required` | **`true`** — aligns with §6a.0 |
| `cost_ceiling_required` | **`true`** — operator-declared planning ceiling (no billing API) |
| `stop_procedure_required` | **`true`** — named stop owner + procedure reference |
| `orphan_detection_required` | **`true`** — orphan resource detection owner required |
| `teardown_owner_required` | **`true`** — named teardown owner before charter |

#### Required contract bindings (reuse-only)

Inventory rows **must** cross-reference (pointer-only):

1. §6a.0 Remote Runtime Command Contract — backend-not-lane; `lane_id=paper` only.
2. §6a.0.1 Local Remote Runner Preflight — dry CLI shape validation.
3. §6a.0.2 Remote-Paper Approval/Command-Packet — non-executable packet pointers.
4. Preflight §2a / §2a.1 — [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py).
5. Preflight §2b.1 — mandatory durable closeout.
6. Registry v1 — [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) §6a metadata defaults.
7. S3 prefix-plan (optional) — [preflight_s3_finalized_evidence_export_v0.py](../../../scripts/ops/preflight_s3_finalized_evidence_export_v0.py) **only** as non-executing transport plan when `evidence_transport=s3_export_after_finalize_plan`; upload does **not** authorize runtime (§6a.3).

#### Forbidden inventory content (fail-closed)

| Forbidden in v0 planning rows | Marker |
|---|---|
| Cloud provider instance ids implying live discovery | `REMOTE_HOST_INVENTORY_FORBIDS_PROVIDER_INSTANCE_IDS=true` |
| AWS/cloud account ids | `REMOTE_HOST_INVENTORY_FORBIDS_ACCOUNT_IDS=true` |
| IP addresses / hostnames resolving to live endpoints | `REMOTE_HOST_INVENTORY_FORBIDS_REAL_IPS=true` |
| SSH usernames, keys, fingerprints | `REMOTE_HOST_INVENTORY_FORBIDS_SSH_USERNAMES_KEYS=true` |
| Credentials, API keys, tokens, secrets | `REMOTE_HOST_INVENTORY_FORBIDS_CREDENTIALS=true` |
| Real S3 bucket names or transport endpoints | `REMOTE_HOST_INVENTORY_FORBIDS_REAL_BUCKET_NAMES=true` |
| Regions requiring provider API interaction | forbidden in v0 fixture/docs examples |
| Start/stop/provision/connect commands | `REMOTE_HOST_INVENTORY_DO_NOT_PROVISION=true`; `REMOTE_HOST_INVENTORY_DO_NOT_CONNECT=true` |

#### Non-authorizing posture (required machine lines)

Future operator tooling may emit inventory summary rows with:

| Line | Allowed values (v0) |
|---|---|
| `REMOTE_HOST_INVENTORY_STATUS` | `planning_only` \| `blocked` \| `invalid` |
| `REMOTE_HOST_INVENTORY_READY_FOR_IMPLEMENTATION_CHARTER` | `false` always in v0 |
| `REMOTE_HOST_INVENTORY_PROVISIONED` | **`false`** |
| `REMOTE_HOST_INVENTORY_CONNECTED` | **`false`** |
| `REMOTE_HOST_INVENTORY_NETWORK_CALLED` | **`false`** |
| `REMOTE_HOST_INVENTORY_AWS_CLI_CALLED` | **`false`** |
| `REMOTE_HOST_INVENTORY_SSH_CALLED` | **`false`** |
| `REMOTE_HOST_INVENTORY_SYSTEMD_CALLED` | **`false`** |
| `REMOTE_HOST_INVENTORY_GHA_RUNNER_IMPLEMENTED` | **`false`** |

#### Implementation posture (this slice)

This contract is **static / normative only** (`REMOTE_HOST_INVENTORY_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true`). It **does not** ship inventory CLI, cloud discovery, provisioning scripts, SSH/systemd/GHA wiring, runner implementation, or dry command templates.

Cross-reference: §6a Remote Runtime Host Metadata; §6a.0–§6a.0.2 remote paper chain; credential boundaries runbook; composition-index §6b orthogonal.

#### 6a.0.4 Remote cost/kill/orphan safety contract v0 (planning-only)

```
REMOTE_COST_KILL_ORPHAN_SAFETY_CONTRACT_V0=true
REMOTE_COST_KILL_ORPHAN_SAFETY_CONTRACT_DOCS_TESTS_ONLY=true
REMOTE_COST_KILL_ORPHAN_PLANNING_ONLY=true
REMOTE_COST_KILL_ORPHAN_DO_NOT_PROVISION=true
REMOTE_COST_KILL_ORPHAN_DO_NOT_CONNECT=true
REMOTE_COST_KILL_ORPHAN_DO_NOT_KILL_PROCESS=true
REMOTE_COST_KILL_ORPHAN_DO_NOT_TERMINATE_HOST=true
REMOTE_COST_KILL_ORPHAN_NO_AWS_CLI=true
REMOTE_COST_KILL_ORPHAN_NO_SSH=true
REMOTE_COST_KILL_ORPHAN_NO_SYSTEMD=true
REMOTE_COST_KILL_ORPHAN_NO_GHA_RUNNER=true
REMOTE_COST_KILL_ORPHAN_NO_NETWORK=true
REMOTE_COST_KILL_ORPHAN_NOT_APPROVAL=true
REMOTE_COST_KILL_ORPHAN_NOT_RUNTIME_START=true
REMOTE_COST_KILL_ORPHAN_NOT_HOST_TERMINATION=true
REMOTE_COST_KILL_ORPHAN_NOT_CREDENTIAL_GRANT=true
REMOTE_COST_KILL_ORPHAN_NOT_TESTNET_OR_LIVE_GATE=true
REMOTE_COST_KILL_ORPHAN_REQUIRES_COST_CEILING=true
REMOTE_COST_KILL_ORPHAN_REQUIRES_MAX_INSTANCE_LIFETIME=true
REMOTE_COST_KILL_ORPHAN_REQUIRES_MAX_RUNTIME_SECONDS=true
REMOTE_COST_KILL_ORPHAN_REQUIRES_STOP_PROCEDURE=true
REMOTE_COST_KILL_ORPHAN_REQUIRES_KILL_PROCEDURE=true
REMOTE_COST_KILL_ORPHAN_REQUIRES_ORPHAN_DETECTION=true
REMOTE_COST_KILL_ORPHAN_REQUIRES_TEARDOWN_OWNER=true
REMOTE_COST_KILL_ORPHAN_REQUIRES_DURABLE_CLOSEOUT=true
REMOTE_COST_KILL_ORPHAN_REQUIRES_MANIFEST_VERIFY=true
REMOTE_COST_KILL_ORPHAN_FORBIDS_REAL_IPS=true
REMOTE_COST_KILL_ORPHAN_FORBIDS_CREDENTIALS=true
REMOTE_COST_KILL_ORPHAN_FORBIDS_ACCOUNT_IDS=true
REMOTE_COST_KILL_ORPHAN_FORBIDS_INSTANCE_IDS=true
REMOTE_COST_KILL_ORPHAN_IMPLEMENTATION_CHARTER_BLOCKED_WITHOUT_SAFETY=true
```

**Purpose:** Define **non-authorizing** remote cost, kill, stop, teardown, and orphan-detection **planning requirements** that must be present and reviewed **before** any future Remote Paper-only **implementation charter** can be considered — **without** provisioning, connecting to, stopping, killing, terminating, or managing any real host or process.

**Normative rule:** No Remote Paper implementation charter is acceptable in v0 unless cost/kill/orphan safety fields are declared, owned, and cross-linked to §6a.0.3 inventory rows (`REMOTE_COST_KILL_ORPHAN_IMPLEMENTATION_CHARTER_BLOCKED_WITHOUT_SAFETY=true`). This contract **does not** execute stop/kill/teardown and **does not** grant runtime or host termination authority.

**Fixture owner (non-authorizing):** [remote_cost_kill_orphan_safety_v0.json](../../../tests/fixtures/ops/remote_cost_kill_orphan_safety_v0.json) — fake planning-only example; **does not** describe live resources or procedures that were executed.

#### Required safety fields (v0)

| Field | Required value / rule |
|---|---|
| `remote_host_id` | Planning-only synthetic id; aligns with §6a.0.3 inventory row |
| `remote_run_id` | Safe run id; aligns with §6a.0 |
| `runtime_backend` | `ec2` \| `vps` \| `gha_runner` \| `data_node` |
| `expected_cost_ceiling` | Operator-declared planning ceiling (currency/unit documented; no billing API) |
| `max_instance_lifetime_seconds` | Positive bounded cap |
| `max_runtime_seconds` | Positive bounded cap; aligns with §6a.0 |
| `stop_procedure_ref` | Pointer to documented stop procedure (planning doc/runbook ref; not executable command) |
| `kill_procedure_ref` | Pointer to documented kill/emergency-stop procedure (planning only) |
| `orphan_detection_ref` | Pointer to orphan detection checklist (planning only) |
| `teardown_owner` | Named owner responsible for teardown planning |
| `cost_owner` | Named owner responsible for cost ceiling oversight |
| `incident_owner` | Named owner for incident/stop escalation |
| `evidence_owner` | Named owner for §2a primary evidence |
| `closeout_owner` | Named owner for §2b.1 durable closeout |
| `orphan_check_required` | **`true`** |
| `teardown_required` | **`true`** |
| `stop_procedure_required` | **`true`** |
| `cost_ceiling_required` | **`true`** |
| `max_runtime_seconds_required` | **`true`** |
| `max_instance_lifetime_required` | **`true`** |
| `durable_closeout_required` | **`true`** |
| `manifest_verify_required` | **`true`** — `MANIFEST.sha256` RC=0 per §2a |

#### Required boundary fields (v0)

| Field | Required value |
|---|---|
| `live_authority` | **`false`** |
| `testnet_authority` | **`false`** |
| `broker_credentials_present` | **`false`** |
| `exchange_credentials_present` | **`false`** |
| `network_called` | **`false`** |
| `aws_cli_called` | **`false`** |
| `ssh_called` | **`false`** |
| `systemd_called` | **`false`** |
| `gha_runner_implemented` | **`false`** |
| `process_control_called` | **`false`** |
| `host_termination_called` | **`false`** |

#### Required contract bindings (reuse-only)

Safety rows **must** cross-reference (pointer-only):

1. §6a.0 Remote Runtime Command Contract — `max_runtime_seconds`, paper-only bounds.
2. §6a.0.1 Local Remote Runner Preflight — dry shape validation.
3. §6a.0.2 Remote-Paper Approval/Command-Packet — non-executable packet pointers.
4. §6a.0.3 Remote Host Inventory Planning — host owner, teardown owner, cost ceiling requirements.
5. Preflight §2a / §2a.1 — [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py).
6. Preflight §2b.1 — mandatory durable closeout.
7. Registry v1 — [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py).

#### Forbidden content (fail-closed)

| Forbidden in v0 planning rows | Marker |
|---|---|
| Real AWS/cloud account ids | `REMOTE_COST_KILL_ORPHAN_FORBIDS_ACCOUNT_IDS=true` |
| Real EC2/provider instance ids | `REMOTE_COST_KILL_ORPHAN_FORBIDS_INSTANCE_IDS=true` |
| IP addresses / live hostnames | `REMOTE_COST_KILL_ORPHAN_FORBIDS_REAL_IPS=true` |
| SSH usernames, keys, credentials, secrets | `REMOTE_COST_KILL_ORPHAN_FORBIDS_CREDENTIALS=true` |
| Real S3 bucket names | forbidden (align with §6a.0.3) |
| Start/stop/kill/terminate/provision/connect commands | `DO_NOT_KILL_PROCESS`; `DO_NOT_TERMINATE_HOST`; inventory `DO_NOT_PROVISION`/`DO_NOT_CONNECT` |

#### Non-authorizing posture (required machine lines)

| Line | Allowed values (v0) |
|---|---|
| `REMOTE_COST_KILL_ORPHAN_STATUS` | `planning_only` \| `blocked` \| `invalid` |
| `REMOTE_COST_KILL_ORPHAN_READY_FOR_IMPLEMENTATION_CHARTER` | **`false` always in v0** |
| `REMOTE_COST_KILL_ORPHAN_PROCESS_KILLED` | **`false`** |
| `REMOTE_COST_KILL_ORPHAN_HOST_TERMINATED` | **`false`** |

#### Implementation posture (this slice)

This contract is **static / normative only** (`REMOTE_COST_KILL_ORPHAN_SAFETY_CONTRACT_DOCS_TESTS_ONLY=true`). It **does not** ship safety enforcement CLI, billing integration, process control, host termination scripts, SSH/systemd/GHA wiring, runner implementation, or dry command templates.

Cross-reference: §6a.0–§6a.0.3 remote paper chain; KillSwitch / incident runbooks as **future pointer targets only** (no authority promotion); composition-index §6b orthogonal.

#### 6a.0.5 Remote paper packet assembly validator planning contract v0 (planning-only)

```
REMOTE_PAPER_PACKET_ASSEMBLY_VALIDATOR_PLANNING_CONTRACT_V0=true
REMOTE_PAPER_PACKET_ASSEMBLY_VALIDATOR_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true
REMOTE_PAPER_PACKET_VALIDATOR_PLANNING_ONLY=true
REMOTE_PAPER_PACKET_VALIDATOR_NO_CLI_IMPLEMENTATION=true
REMOTE_PAPER_PACKET_VALIDATOR_DO_NOT_RUN=true
REMOTE_PAPER_PACKET_VALIDATOR_NO_RUNNER_IMPLEMENTATION=true
REMOTE_PAPER_PACKET_VALIDATOR_NO_DRY_COMMAND_TEMPLATE=true
REMOTE_PAPER_PACKET_VALIDATOR_NO_AWS_CLI=true
REMOTE_PAPER_PACKET_VALIDATOR_NO_SSH=true
REMOTE_PAPER_PACKET_VALIDATOR_NO_SYSTEMD=true
REMOTE_PAPER_PACKET_VALIDATOR_NO_GHA_RUNNER=true
REMOTE_PAPER_PACKET_VALIDATOR_NO_NETWORK=true
REMOTE_PAPER_PACKET_VALIDATOR_NO_PROCESS_CONTROL=true
REMOTE_PAPER_PACKET_VALIDATOR_REQUIRES_PREFLIGHT_JSON=true
REMOTE_PAPER_PACKET_VALIDATOR_REQUIRES_APPROVAL_PACKET=true
REMOTE_PAPER_PACKET_VALIDATOR_REQUIRES_HOST_INVENTORY=true
REMOTE_PAPER_PACKET_VALIDATOR_REQUIRES_COST_KILL_ORPHAN_SAFETY=true
REMOTE_PAPER_PACKET_VALIDATOR_REQUIRES_REGISTRY_V1=true
REMOTE_PAPER_PACKET_VALIDATOR_S3_PREFIX_PLAN_OPTIONAL_NON_EXECUTING=true
REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_IMPLEMENTATION_CHARTER=false
REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_START=false
REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_DRY_COMMAND_TEMPLATE=false
REMOTE_PAPER_PACKET_VALIDATOR_NOT_APPROVAL=true
REMOTE_PAPER_PACKET_VALIDATOR_NOT_RUNTIME_START=true
REMOTE_PAPER_PACKET_VALIDATOR_DRY_TEMPLATE_BLOCKED_UNTIL_VALIDATOR_PLANNING=true
```

**Purpose:** Define a **planning-only, offline** validator contract describing how existing remote-paper planning artifacts must be **cross-checked** before any dry command template or implementation charter can be considered — **without** implementing a validator CLI, assembling executable commands, starting runners, or inspecting real archives/cloud resources.

**Normative rule:** This contract **does not** approve implementation, approve start, replace scheduler guard, HOLD binding, Preflight §2a/§2a.1, §2b.1 durable closeout, or Registry v1. S3/Notion/Dashboard remain non-authoritative.

**Fixture owner (non-authorizing):** [remote_paper_packet_assembly_validator_planning_v0.json](../../../tests/fixtures/ops/remote_paper_packet_assembly_validator_planning_v0.json) — planning-only cross-artifact index; **does not** execute validation.

#### Required bound artifacts (v0)

| Artifact | Owner |
|---|---|
| Preflight JSON shape | §6a.0.1 [preflight_remote_runtime_runner_v0.py](../../../scripts/ops/preflight_remote_runtime_runner_v0.py) |
| Approval/command packet | §6a.0.2 [remote_paper_approval_command_packet_v0.json](../../../tests/fixtures/ops/remote_paper_approval_command_packet_v0.json) |
| Host inventory | §6a.0.3 [remote_host_inventory_planning_v0.json](../../../tests/fixtures/ops/remote_host_inventory_planning_v0.json) |
| Cost/kill/orphan safety | §6a.0.4 [remote_cost_kill_orphan_safety_v0.json](../../../tests/fixtures/ops/remote_cost_kill_orphan_safety_v0.json) |
| Registry v1 row/pointer | [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) |
| S3 prefix-plan (optional) | [preflight_s3_finalized_evidence_export_v0.py](../../../scripts/ops/preflight_s3_finalized_evidence_export_v0.py) when `evidence_transport=s3_export_after_finalize_plan` |

#### Required cross-artifact consistency fields

All bound artifacts **must agree** on:

| Field | Rule |
|---|---|
| `remote_run_id` | Same safe run id across packet, safety, and preflight planning rows |
| `runtime_host` | `remote` |
| `runtime_backend` | Same enum across artifacts |
| `runtime_mode` | `paper_only` |
| `lane_id` | `paper` |
| `remote_host_id` | Same planning synthetic id across inventory and safety |
| `max_runtime_seconds` | Consistent bounded cap |
| `evidence_root_type` | `remote_durable` |
| `evidence_transport` | Consistent; optional S3 prefix-plan only when planned |
| `live_authority` | **`false`** |
| `testnet_authority` | **`false`** |
| `broker_credentials_present` | **`false`** |
| `exchange_credentials_present` | **`false`** |

#### Future validator output semantics (non-authorizing)

| Line | Allowed values (v0) |
|---|---|
| `REMOTE_PAPER_PACKET_VALIDATOR_STATUS` | `planning_valid` \| `blocked` \| `invalid` |
| `REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_IMPLEMENTATION_CHARTER` | **`false` always in v0** |
| `REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_START` | **`false` always in v0** |
| `REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_DRY_COMMAND_TEMPLATE` | **`false` always in v0** |
| `REMOTE_PAPER_PACKET_VALIDATOR_RUNTIME_COMMANDS_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_VALIDATOR_AWS_CLI_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_VALIDATOR_NETWORK_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_VALIDATOR_SSH_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_VALIDATOR_SYSTEMD_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_VALIDATOR_GHA_RUNNER_IMPLEMENTED` | **`false`** |
| `REMOTE_PAPER_PACKET_VALIDATOR_PROCESS_CONTROL_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_VALIDATOR_HOST_TERMINATION_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_VALIDATOR_S3_UPLOAD_CALLED` | **`false`** |
| `REMOTE_PAPER_PACKET_VALIDATOR_S3_DOWNLOAD_CALLED` | **`false`** |

`planning_valid` means cross-artifact planning fields align — it **still does not** authorize implementation, dry command templates, or runtime start.

#### Dry command template gate (normative)

Dry command templates remain **blocked** until:

1. This validator planning contract exists (`REMOTE_PAPER_PACKET_VALIDATOR_DRY_TEMPLATE_BLOCKED_UNTIL_VALIDATOR_PLANNING=true`).
2. Closeout enforcement planning contract reviewed (Preflight §2b.2; `CLOSEOUT_ENFORCEMENT_REVIEW_REQUIRED_BEFORE_DRY_COMMAND_TEMPLATE=true`).
3. Operator explicitly charters a **separate non-executable** dry-command-template slice.

#### Forbidden content

No real secrets, account IDs, IPs, provider instance IDs, bucket names, SSH usernames, or credentials in validator planning rows or fixture examples.

#### Implementation posture (this slice)

This contract is **static / normative only** (`REMOTE_PAPER_PACKET_ASSEMBLY_VALIDATOR_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true`). It **does not** ship assembly-validator CLI, archive walkers, cloud inspection, runner implementation, dry command templates, or process control (§6a.0.6 owns the separate offline packet validator CLI).

Cross-reference: §6a.0–§6a.0.4 remote paper chain; §6a.0.6 validator CLI planning; composition-index §6b orthogonal.

#### 6a.0.6 Remote paper validator CLI contract v0 (planning contract + implemented offline CLI)

```
REMOTE_PAPER_VALIDATOR_CLI_PLANNING_CONTRACT_V0=true
REMOTE_PAPER_VALIDATOR_CLI_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true
REMOTE_PAPER_VALIDATOR_CLI_IMPLEMENTED=true
REMOTE_PAPER_VALIDATOR_CLI_OFFLINE_STATIC_ONLY=true
REMOTE_PAPER_VALIDATOR_CLI_NO_RUNTIME=true
REMOTE_PAPER_VALIDATOR_CLI_NO_NETWORK=true
REMOTE_PAPER_VALIDATOR_CLI_NO_AWS=true
REMOTE_PAPER_VALIDATOR_CLI_NO_SSH=true
REMOTE_PAPER_VALIDATOR_CLI_NO_SYSTEMD=true
REMOTE_PAPER_VALIDATOR_CLI_NO_ARCHIVE_WALKER=true
REMOTE_PAPER_VALIDATOR_CLI_NO_ARCHIVE_MUTATION=true
REMOTE_PAPER_VALIDATOR_CLI_NO_DRY_COMMAND_TEMPLATE=true
REMOTE_PAPER_VALIDATOR_CLI_NO_REMOTE_RUNNER=true
REMOTE_PAPER_VALIDATOR_CLI_READY_FOR_IMPLEMENTATION=false
REMOTE_PAPER_VALIDATOR_CLI_READY_FOR_START=false
REMOTE_PAPER_VALIDATOR_CLI_PREFLIGHT_BLOCKED_LIFTED=false
REMOTE_RUNNER_START_PERMITTED=false
STAGE3_RUNNER_START_CHARTER_PERMITTED=false
REMOTE_PAPER_VALIDATOR_CLI_OUTPUT_STATUS_ENUM_PASS_BLOCKED_INVALID=true
REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_RUNTIME=true
REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_REMOTE_RUNNER=true
REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_LIVE=true
REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_TESTNET=true
REMOTE_PAPER_VALIDATOR_CLI_IMPLEMENTATION_REQUIRES_OPERATOR_CHARTER=true
```

**Purpose:** Define the Remote Paper packet validator **CLI contract** (input paths, validation rules, JSON output) and record the **implemented offline CLI** on `main` — **without** granting runtime authority, lifting Preflight **BLOCKED**, authorizing remote runner implementation/start, emitting `command_template`, or permitting Stage-3 runner start charter.

**Implemented CLI (non-authorizing):** [validate_remote_paper_packet_v0.py](../../../scripts/ops/validate_remote_paper_packet_v0.py) (`OP-REMOTE-PAPER-VALIDATOR-CLI-IMPL-V0`) — offline/static local JSON validation only; explicit input paths; status enum `PASS` \| `BLOCKED` \| `INVALID`.

**Normative rule:** `REMOTE_PAPER_VALIDATOR_CLI_IMPLEMENTED=true` — the offline validator CLI ships on `main`. `REMOTE_PAPER_VALIDATOR_CLI_OFFLINE_STATIC_ONLY=true` — reads local JSON files only; no archive walker, network, AWS, SSH, systemd, Docker, or runtime inspection. `REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_RUNTIME=true` — **`PASS` does not authorize runtime**. `REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_REMOTE_RUNNER=true` — **`PASS` does not authorize remote runner implementation or start**. `REMOTE_PAPER_VALIDATOR_CLI_PREFLIGHT_BLOCKED_LIFTED=false` — **`PASS` does not clear Preflight BLOCKED**. `REMOTE_PAPER_VALIDATOR_CLI_READY_FOR_START=false` — **`PASS` does not set `READY_FOR_START=true`**. `REMOTE_RUNNER_START_PERMITTED=false` and `STAGE3_RUNNER_START_CHARTER_PERMITTED=false` — Stage-3 runner start charter remains forbidden. `authority.command_template` / CLI output **must not** emit executable `command_template` (`REMOTE_PAPER_VALIDATOR_CLI_NO_DRY_COMMAND_TEMPLATE=true`).

**Relationship to §6a.0.5:** §6a.0.5 defines **assembly cross-check semantics** (`planning_valid` / `blocked` / `invalid`). This §6a.0.6 defines the **implemented local CLI** that consumes explicit JSON inputs and emits machine-readable results — still **non-authorizing**.

**Fixture owner (non-authorizing):** [remote_paper_validator_cli_planning_v0.json](../../../tests/fixtures/ops/remote_paper_validator_cli_planning_v0.json) — CLI contract index aligned with this section; the JSON fixture is **not** a runnable command.

#### CLI input shape (local JSON only)

| Input | Required | Rule |
|---|---|---|
| `--preflight-json` | **yes** | Path to local §6a.0.1 preflight output JSON (or planning fixture); **no** live preflight execution in v0 planning |
| `--approval-packet` | **yes** | [remote_paper_approval_command_packet_v0.json](../../../tests/fixtures/ops/remote_paper_approval_command_packet_v0.json) or equivalent local file |
| `--host-inventory` | **yes** | [remote_host_inventory_planning_v0.json](../../../tests/fixtures/ops/remote_host_inventory_planning_v0.json) or equivalent |
| `--cost-kill-orphan-safety` | **yes** | [remote_cost_kill_orphan_safety_v0.json](../../../tests/fixtures/ops/remote_cost_kill_orphan_safety_v0.json) or equivalent |
| `--registry-json` | **yes** | Local Registry v1 JSON export or registry fixture row; **no** archive walk |
| `--s3-prefix-plan` | optional | Local §6a.3.1 dry prefix-plan JSON only when `evidence_transport` requires it |
| `--closeout-metadata` | optional | Local JSON summary of §2b.1/§2b.2 closeout fields (readme/manifest/index pointers); **no** copy/verify execution |

**Forbidden inputs (v0 planning):**

- `REMOTE_PAPER_VALIDATOR_CLI_NO_ARCHIVE_WALKER=true` — no automatic discovery under operator `Documents` archive roots or `Peak_Trade_runtime_evidence_archive_*`; no default archive root.
- `REMOTE_PAPER_VALIDATOR_CLI_NO_NETWORK=true` — no HTTP, S3 listing, provider APIs, or SSH probes.
- `REMOTE_PAPER_VALIDATOR_CLI_NO_RUNTIME=true` — no live process, container, or Docker inspection.
- No implicit glob over repo `out/` or operator home directories.

#### CLI validations (offline rules)

The implemented CLI **must** fail closed (`INVALID` or `BLOCKED`) when any of the following hold:

| Check | Rule |
|---|---|
| `remote_run_id` | Consistent across packet, inventory, safety, and preflight rows |
| `lane_id` | **`paper` only** |
| `runtime_mode` | **`paper_only` only** |
| Backend-not-lane | `runtime_backend` is metadata only; **`remote_runtime` is not a lane**; **`daemon_paper_24h` is not a lane** (§6b composition only) |
| Preflight | [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) remains **`BLOCKED`** unless a **future explicit charter** changes it — CLI `PASS` does **not** clear BLOCKED |
| Packet authority | `DO_NOT_RUN=true`, `READY_FOR_START=false`, `READY_FOR_IMPLEMENTATION_CHARTER=false` |
| Inventory | Synthetic planning ids only; **no** real IPs, provider instance ids, account ids, SSH users, or credentials |
| Safety | Cost ceiling, `max_runtime_seconds`, stop/kill/orphan/teardown/incident/evidence/closeout owners present per §6a.0.4 |
| S3 prefix-plan | If provided: local-only, non-secret, no `s3:&#47;&#47;` bucket ARNs in fixture examples |
| Closeout | §2b.1 and §2b.2 requirements **referenced** in optional metadata only — CLI does **not** execute copy/verify or mutate archives |
| Authority substitutes | Notion, Market Dashboard, and S3 upload/export success **do not** substitute for packet/preflight authority |

#### CLI output shape (JSON only)

`REMOTE_PAPER_VALIDATOR_CLI_OUTPUT_STATUS_ENUM_PASS_BLOCKED_INVALID=true` — status enum: `PASS` \| `BLOCKED` \| `INVALID`.

| Field | Semantics |
|---|---|
| `status` | `PASS` \| `BLOCKED` \| `INVALID` |
| `reasons` | String list of fail-closed reasons |
| `checked_artifacts` | Basenames/paths of inputs validated (local paths only) |
| `authority.runtime_authorized` | **`false` always in v0** |
| `authority.remote_runner_authorized` | **`false` always in v0** |
| `authority.live_authorized` | **`false` always in v0** |
| `authority.testnet_authorized` | **`false` always in v0** |
| `command_template` | **absent** — `REMOTE_PAPER_VALIDATOR_CLI_NO_DRY_COMMAND_TEMPLATE=true`; no shell command emission |

**Non-authorizing PASS semantics:**

- `REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_RUNTIME=true`
- `REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_REMOTE_RUNNER=true`
- `REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_LIVE=true`
- `REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_TESTNET=true`

#### Implementation gates

- `REMOTE_PAPER_VALIDATOR_CLI_IMPLEMENTATION_REQUIRES_OPERATOR_CHARTER=true` — initial CLI implementation shipped under **OP-REMOTE-PAPER-VALIDATOR-CLI-IMPL-V0**; must remain **offline/static** (read JSON files, write JSON result).
- `REMOTE_PAPER_VALIDATOR_CLI_READY_FOR_IMPLEMENTATION=false` — this contract slice does **not** authorize further implementation beyond the chartered offline CLI.
- `REMOTE_PAPER_VALIDATOR_CLI_NO_REMOTE_RUNNER=true` — the validator CLI **does not** implement or start remote runners.
- **Dry command template** remains blocked until: §6a.0.5 assembly planning exists; §2b.2 closeout enforcement planning merged; **this §6a.0.6 implemented CLI reviewed**; operator charters a **separate non-executable** dry-command-template slice.

#### Bindings

- §2a primary evidence retention — Preflight owner; CLI does not satisfy §2a.
- §2b.1 mandatory durable closeout — referenced via optional metadata only.
- §2b.2 closeout enforcement planning — referenced; CLI does **not** execute closeout copy/verify by default ([durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py) is a separate non-authorizing helper).
- §6a.0–§6a.0.5 remote paper planning chain — sole semantic inputs.
- §6a.3 / §6a.3.1 S3 finalized evidence dry/prefix-plan — optional local prefix-plan input only.

#### Implementation posture (this slice)

This contract documents the **implemented offline validator CLI** and remains **non-authorizing** (`REMOTE_PAPER_VALIDATOR_CLI_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true` for contract-doc/tests alignment only). It **does not** lift Preflight **BLOCKED**, authorize runner start, ship remote runners, emit dry command templates, or grant Stage-3 start charter authority.

Cross-reference: §6a.0.5 assembly validator planning; §6a.0.7 dry command template planning; composition-index §6b orthogonal.

#### 6a.0.7 Remote paper dry command template planning contract v0 (planning-only)

```
REMOTE_PAPER_DRY_COMMAND_TEMPLATE_PLANNING_CONTRACT_V0=true
REMOTE_PAPER_DRY_COMMAND_TEMPLATE_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true
DRY_COMMAND_TEMPLATE_PLANNING_ONLY=true
DRY_COMMAND_TEMPLATE_DO_NOT_RUN=true
DRY_COMMAND_TEMPLATE_NON_EXECUTABLE=true
DRY_COMMAND_TEMPLATE_EXECUTION_PERMITTED=false
DRY_COMMAND_TEMPLATE_READY_FOR_START=false
DRY_COMMAND_TEMPLATE_PLANNING_ARTIFACT_PRESENT=true
DRY_COMMAND_TEMPLATE_NOT_IN_APPROVAL_PACKET=true
DRY_COMMAND_TEMPLATE_NOT_EMITTED_BY_VALIDATOR_CLI=true
DRY_COMMAND_TEMPLATE_PREFLIGHT_BLOCKED_UNCHANGED=true
DRY_COMMAND_TEMPLATE_NO_RUNTIME=true
DRY_COMMAND_TEMPLATE_NO_NETWORK=true
DRY_COMMAND_TEMPLATE_NO_AWS=true
DRY_COMMAND_TEMPLATE_NO_SSH=true
DRY_COMMAND_TEMPLATE_NO_SYSTEMD=true
DRY_COMMAND_TEMPLATE_NO_GHA_RUNNER=true
DRY_COMMAND_TEMPLATE_NO_RCLONE=true
DRY_COMMAND_TEMPLATE_NO_DOCKER=true
DRY_COMMAND_TEMPLATE_NO_PROCESS_CONTROL=true
DRY_COMMAND_TEMPLATE_NO_REMOTE_RUNNER=true
DRY_COMMAND_TEMPLATE_NO_VALIDATOR_CLI_IMPLEMENTATION=true
DRY_COMMAND_TEMPLATE_DOES_NOT_INVOKE_CLOSEOUT_HELPER=true
DRY_COMMAND_TEMPLATE_NO_NOTION_WRITE=true
DRY_COMMAND_TEMPLATE_NO_MARKET_DASHBOARD_CHANGE=true
```

**Purpose:** Define a **planning-only, non-executable** dry command template **contract index** — structured operator-review steps and authority boundaries — **without** runnable shell one-liners, **without** shipping executable scripts, **without** invoking [durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py), and **without** authorizing runtime, remote runner start, Validator CLI execution, AWS/EC2/GHA/systemd/SSH/rclone/S3 transport, Notion writes, Market Dashboard changes, Testnet, Live, or broker/exchange access.

**Normative rule:** `DRY_COMMAND_TEMPLATE_PLANNING_ONLY=true` — static contract + fixture + tests only. `DRY_COMMAND_TEMPLATE_NON_EXECUTABLE=true` — no shebang, no `chmod +x`, no copy-paste start commands. `DRY_COMMAND_TEMPLATE_DO_NOT_RUN=true` — operators must not treat this artifact as a command to execute.

**Relationship to §6a.0.5 / §6a.0.6:** §6a.0.5 defines assembly cross-check semantics; §6a.0.6 defines implemented Validator CLI I/O (**`REMOTE_PAPER_VALIDATOR_CLI_NO_DRY_COMMAND_TEMPLATE=true`** — CLI must **not** emit `command_template`). This §6a.0.7 is the **separate planning artifact** permitted after operator charter Gate 3; it **does not** satisfy execution gates and **`DRY_COMMAND_TEMPLATE_EXECUTION_PERMITTED=false`** always in v0.

**Fixture owner (non-authorizing):** [remote_paper_dry_command_template_planning_v0.json](../../../tests/fixtures/ops/remote_paper_dry_command_template_planning_v0.json) — illustrative review steps only; **does not** execute.

#### Subordination (must reuse; do not replace)

- §6a.0 Remote Runtime Command Contract v0 — metadata/gate shape owner
- §6a.0.2 Remote paper approval/command packet — **no** `command_template` field in packet
- §6a.0.5 Packet assembly validator planning — cross-artifact semantics
- §6a.0.6 Validator CLI planning — no template emission from CLI output
- §2b.1 Mandatory Durable Closeout Contract v0 — completeness owner
- §2b.2 Closeout Enforcement Planning Contract v0 — enforcement/helper classification

#### Illustrative steps (fixture; operator manual review only)

Each step in the fixture uses `mode=operator_manual_review_only`, `executable_command=null`, `command_line=null`, `starts_runtime=false`, `authority=false`. Steps name **contracts and fixtures** to read — not commands to run.

#### Forbidden artifact content

No real secrets, hostnames, IPs, provider instance IDs, bucket ARNs, account IDs, SSH users, credentials, runnable one-liners, or `command_template` fields inside the approval packet.

#### Non-authority (explicit)

- `DRY_COMMAND_TEMPLATE_PREFLIGHT_BLOCKED_UNCHANGED=true` — [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) remains **BLOCKED**; this artifact does not clear BLOCKED.
- `DRY_COMMAND_TEMPLATE_READY_FOR_START=false` — does not set `REMOTE_PAPER_PACKET_READY_FOR_START` or any start authority.
- Notion and Market Dashboard remain projection-only (§6a.1 / §6a.2).

#### Implementation posture (this slice)

This contract is **static / normative only** (`REMOTE_PAPER_DRY_COMMAND_TEMPLATE_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true`). It **does not** ship runnable templates, execute Validator CLI, invoke Closeout Helper (`DRY_COMMAND_TEMPLATE_DOES_NOT_INVOKE_CLOSEOUT_HELPER=true`), implement remote runners, or perform process control.

Cross-reference: §6a.0.6 validator CLI planning; composition-index §6b orthogonal.

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

### 6a.0.8 Post-Closeout Projection Automation Charter v0 (docs/tests-only)

```
POST_CLOSEOUT_PROJECTION_AUTOMATION_V0=true
NOTION_POST_CLOSEOUT_SYNC_V0=true
MARKET_DASHBOARD_READONLY_RUN_PROJECTION_V0=true
POST_CLOSEOUT_PROJECTION_AUTOMATION_ENABLED=false
NOTION_POST_CLOSEOUT_SYNC_ENABLED=false
MARKET_DASHBOARD_RUN_PROJECTION_ENABLED=false
NOTION_AUTHORITY=false
MARKET_DASHBOARD_AUTHORITY=false
RUNTIME_CONTROL_FROM_PROJECTION=false
DASHBOARD_RUNTIME_CONTROL=false
LIVE_AUTHORITY=false
TESTNET_AUTHORITY=false
BROKER_EXCHANGE_AUTHORITY=false
PROJECTION_AFTER_CLOSEOUT_ONLY=true
PROJECTION_AFTER_MANIFEST_VERIFY_ONLY=true
REPO_AND_DURABLE_EVIDENCE_REMAIN_CANONICAL=true
NOTION_IS_PROJECTION_ONLY=true
MARKET_DASHBOARD_IS_PROJECTION_ONLY=true
NO_PARALLEL_MARKET_SURFACE=true
NO_PARALLEL_NOTION_DB=true
NO_PARALLEL_READMODEL=true
POST_CLOSEOUT_PROJECTION_AUTOMATION_DOCS_TESTS_ONLY=true
```

**Purpose:** Bind **Notion post-closeout sync** (§6a.1), **Market Dashboard read-only run projection** (§6a.2), and the **shared Registry v1 projection feed** into one operator-facing automation charter — **without** enabling sync, dashboard overlays, payload builders, hooks, or runtime actions in this slice.

**Normative chain (future automation may follow; default off):**

1. Material closeout complete on durable evidence **outside `/tmp`** per Preflight §2b.1 (`PROJECTION_AFTER_CLOSEOUT_ONLY=true`).
2. `MANIFEST.sha256` verify **RC=0** on the durable root before any projection consumer treats evidence as displayable (`PROJECTION_AFTER_MANIFEST_VERIFY_ONLY=true`).
3. Build [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) JSON only — **sole feed**; do not walk `DURABLE_ARCHIVE_ROOT` ad hoc.
4. Optional future consumers (Notion §6a.1, Dashboard §6a.2) remain **projection-only**; repo contracts, manifests, closeouts, and explicit operator approvals stay canonical (`REPO_AND_DURABLE_EVIDENCE_REMAIN_CANONICAL=true`).

**Sub-contract owners (reuse; do not duplicate):**

| Charter alias | Owner |
|---|---|
| `NOTION_POST_CLOSEOUT_SYNC_V0` | §6a.1 — `notion_projection` states; default `disabled`; operator token future-only |
| `MARKET_DASHBOARD_READONLY_RUN_PROJECTION_V0` | §6a.2 — `market_dashboard_projection` states; `GET &#47;market` only; Double Play untouched |
| Shared pointer/status fields | [projection_consumer_v0.py](../../../tests/fixtures/ops/generic_evidence_run_registry_v1/projection_consumer_v0.py) test constants aligned with Registry v1 `runs[]` / `compositions[]` |

**Forbidden in v0 charter slice:** Notion MCP/API writes; new Notion DB schema as productive SSOT; dashboard HTML/template panels or new routes; payload-builder scripts; CI hooks that start runtime; S3/AWS/rclone upload or download; scheduler/daemon/adapter execution; workflow dispatch; Live/Testnet/broker/exchange authority; Master V2 / Double Play route or authority changes; parallel Market Surface, Notion DB, or readmodel SSOT (`NO_PARALLEL_*=true`).

**Implementation posture:** `POST_CLOSEOUT_PROJECTION_AUTOMATION_ENABLED=false`, `NOTION_POST_CLOSEOUT_SYNC_ENABLED=false`, `MARKET_DASHBOARD_RUN_PROJECTION_ENABLED=false` until explicit future operator-chartered slices opt in. This section is **contract/tests-only** (`POST_CLOSEOUT_PROJECTION_AUTOMATION_DOCS_TESTS_ONLY=true`).

Cross-reference: [MARKET_SURFACE_V0.md](../../webui/MARKET_SURFACE_V0.md) (future registry overlay on `GET &#47;market`); [DOCS_TRUTH_MAP.md](../registry/DOCS_TRUTH_MAP.md); Preflight §2b.1 mandatory durable closeout.

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
S3_EXPORT_PREFLIGHT_CLI_IMPLEMENTED=true
S3_UPLOAD_AUTHORITY=false
S3_DOWNLOAD_AUTHORITY=false
```

**Purpose:** Define when Registry v1 may represent `evidence_transport=s3_export_after_finalize` and when a remote/object-storage copy may be **accepted** for closeout/review — **without** S3 upload/download **implementation** in this gate slice, **without** AWS/rclone calls, and **without** a parallel manifest truth layer. S3 evidence transport **planning** exists here; the **implemented** local-only dry preflight CLI is documented in §6a.3.1 (`S3_EXPORT_PREFLIGHT_CLI_NON_AUTHORIZING=true`).

**Canonical owners (reuse):**

- Finalize + manifest verify: [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) — `finalize_primary_evidence_root()`, `MANIFEST.sha256`
- Registry v1 metadata: [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) — §6a `evidence_transport`, `manifest_verified`, `evidence_status`
- Local-only dry preflight CLI: §6a.3.1 — [preflight_s3_finalized_evidence_export_v0.py](../../../scripts/ops/preflight_s3_finalized_evidence_export_v0.py) (operator-invoked; no upload/download/network)
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
S3_EXPORT_PREFLIGHT_CLI_IMPLEMENTED=true
S3_EXPORT_PREFLIGHT_CLI_LOCAL_ONLY=true
S3_EXPORT_PREFLIGHT_CLI_NON_AUTHORIZING=true
S3_UPLOAD_AUTHORITY=false
S3_DOWNLOAD_AUTHORITY=false
AWS_CLI_AUTHORITY=false
RCLONE_AUTHORITY=false
NETWORK_AUTHORITY=false
RUNTIME_INTEGRATION_AUTHORITY=false
REMOTE_RUNNER_START_PERMITTED=false
PRE_FLIGHT_BLOCKED_LIFTED=false
READY_FOR_START=false
STAGE3_RUNNER_START_CHARTER_PERMITTED=false
```

**Purpose:** Define the **implemented** local-only S3 finalized-evidence export **dry preflight CLI** contract and checklist — bridging §6a.3 gate rules to extend-only Phase T/W planning surfaces — **without** AWS/rclone calls, **without** S3 upload/download/list, **without** network, **without** a parallel manifest truth layer, **without** mutating durable archives, and **without** lifting Preflight **BLOCKED**, `READY_FOR_START`, remote runner start, or Stage-3 start charter.

**Normative rule:** `S3_EXPORT_PREFLIGHT_CLI_IMPLEMENTED=true` — [preflight_s3_finalized_evidence_export_v0.py](../../../scripts/ops/preflight_s3_finalized_evidence_export_v0.py) ships on `main`. `S3_EXPORT_PREFLIGHT_CLI_LOCAL_ONLY=true` — reads local evidence roots and Registry JSON only; `--dry-run` and `--no-network` required. `S3_EXPORT_PREFLIGHT_CLI_NON_AUTHORIZING=true` — preflight **PASS** does **not** authorize upload, download, runtime, scheduler clearance, or gate lift. `S3_UPLOAD_AUTHORITY=false`, `S3_DOWNLOAD_AUTHORITY=false`, `AWS_CLI_AUTHORITY=false`, `RCLONE_AUTHORITY=false`, `NETWORK_AUTHORITY=false` — no cloud transport in this slice.

**Canonical owners (reuse):**

- Gate contract: §6a.3 above (export eligibility + consumer acceptance)
- Finalize + manifest verify: [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) — `finalize_primary_evidence_root()`, `verify_manifest_sha256()`, `MANIFEST.sha256`
- Registry v1 metadata: [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) — §6a fields; constants `S3_FINALIZED_EVIDENCE_EXPORT_IMPLEMENTATION_PREFLIGHT_V0`
- Projection consumer fixtures: [projection_consumer_v0.py](../../../tests/fixtures/ops/generic_evidence_run_registry_v1/projection_consumer_v0.py) — `S3_RELEVANT_PROJECTION_FIELDS`
- Extend-only Phase surfaces: [PHASE_T_DATA_NODE_EXPORT_CHANNEL.md](../runbooks/PHASE_T_DATA_NODE_EXPORT_CHANNEL.md), [PHASE_W_EXPORT_PACK_GH_CONSUMER.md](../runbooks/PHASE_W_EXPORT_PACK_GH_CONSUMER.md)

#### Implemented local-only dry preflight CLI (non-authorizing)

**Implementation owner:** [preflight_s3_finalized_evidence_export_v0.py](../../../scripts/ops/preflight_s3_finalized_evidence_export_v0.py) — local-only dry preflight CLI (`--evidence-root`, `--dry-run`, `--no-network` required; optional `--registry-json`, `--run-id`, `--lane-id`, `--export-prefix-plan` for non-executing export-prefix-plan JSON; **no** upload/download/network/AWS/rclone).

Contract shape (v0):

| Input / flag | Required | Semantics (v0) |
|---|---|---|
| `--evidence-root` / `--durable-evidence-root` | yes | Absolute path to finalized durable primary evidence root (**outside** `/tmp`) |
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

Before the dry preflight CLI may recommend `evidence_transport=s3_export_after_finalize`:

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

#### Forbidden (implementation preflight CLI)

- Upload before finalize; active staging sync; acceptance without download+verify
- Secrets/credentials in Registry / Notion / Dashboard projections
- Runtime, scheduler clearance, live/testnet/broker/exchange/strategy authority
- Notion sync authority; Market Dashboard status authority; Double Play / Master V2 authority
- Registry v2; new lane; `lane_id=daemon_paper_24h`; `lane_id=remote_runtime`
- AWS CLI, rclone, S3 upload/download execution in this preflight slice
- `SHA256SUMS.stable.txt` as parallel truth or authority

#### Canonical boundary copy (required on S3 preflight surfaces)

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
