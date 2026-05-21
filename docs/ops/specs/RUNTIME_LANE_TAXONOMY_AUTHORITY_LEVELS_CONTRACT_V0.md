---
docs_token: DOCS_TOKEN_RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0
status: draft
scope: docs-only, non-authorizing runtime lane taxonomy and authority levels
last_updated: 2026-05-21
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
| Shared primary evidence finalize helper | [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) |
| Generic Evidence Run Registry v1 | [build_generic_evidence_run_registry_v1.py](../../../scripts/ops/build_generic_evidence_run_registry_v1.py) |
| Vocabulary forbidden equalities | [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) |
| OPS Cockpit non-authority | [OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1.md](OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1.md) |
| F5 read-only market dashboard (display) | [FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) |
| Readiness Evidence Ledger v0 | [build_readiness_evidence_ledger_v0.py](../../../scripts/ops/build_readiness_evidence_ledger_v0.py) |
| Readiness Ledger Preflight Mirror v0 | [report_readiness_ledger_preflight_mirror_v0.py](../../../scripts/ops/report_readiness_ledger_preflight_mirror_v0.py) |
| Readiness Gate Snapshot v0 | [report_readiness_gate_snapshot_v0.py](../../../scripts/ops/report_readiness_gate_snapshot_v0.py) |
| Credential boundaries | [RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md](../runbooks/RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md) |

**Rule:** This spec is the **lane ID index**. Retention rules remain in preflight §2a/§2b.

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
- p91 status playbooks may still default to runtime `OUT_DIR` P79; post-stop wrapper hints are not wired there in v0.

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
- P101/P93 emit non-executing post-stop hints referencing this wrapper; hints do not auto-execute wrapper, pack, or P79.
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
- p91 status playbooks may still default to runtime `OUT_DIR` P79; post-stop wrapper hints are not wired there in v0.
- In-process online-daemon automatic pack remains **not implemented** (see §7c).

Detail owner: [p93_online_readiness_status_dashboard_v1.sh](../../../scripts/ops/p93_online_readiness_status_dashboard_v1.sh).

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
