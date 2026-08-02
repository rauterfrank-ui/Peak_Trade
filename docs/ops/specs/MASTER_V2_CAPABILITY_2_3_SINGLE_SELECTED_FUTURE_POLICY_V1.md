# CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1

---
docs_token: DOCS_TOKEN_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1
STATUS: CAPABILITY_AVAILABLE
scope: Productive deterministic SINGLE_SELECTED_FUTURE selection authority + atomic persistence + restart proof
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY_ADDED: true
ALPHA_AUTHORITY_ADDED: false
CORE_LOGIC_CHANGE: false
ACTIVATION_STATE: CODE_EXISTS_BOUND_PERSISTED_RESTART_PROVEN_NOT_ACTIVATED
HARD_STOP: true
---

```text
CAPABILITY_ID=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1
TITLE=Single Selected Future Policy (Capability 2.3)
OWNER_REQUIREMENT=Consume Cap 2.2 ranking snapshot; produce deterministic single selected future with hysteresis, min holding, open-position replacement-pending semantics, atomic persistence and restart proof; no alpha/execution/runtime activation
CURRENT_STATE=CODE_EXISTS+BOUND+RUNTIME_REACHABLE+PERSISTED+RESTART_PROVEN; ACTIVATED=false; MULTI_FUTURE/ALPHA/RUNTIME_BINDING not granted
TARGET_STATE=SINGLE_SELECTED_FUTURE selection authority available for later Capability 2.4 runtime binding without live activation
OUT_OF_SCOPE=Master V2/Double Play/Bull-Bear/Dynamic Scope/Composition/Confirmation/Risk/Safety mutation/Exit mutation/Volatility Enforcement/Authorization Consumption/Session Lifecycle/Live/Testnet/Paper Activation/Rulesets/Notion/Dashboard Authority/Top-N Active Set/Runtime Binding
AUTHORITY_OWNER=ops.single_selected_future_policy_v1
PRODUCTIVE_ENTRYPOINT=scripts/ops/run_single_selected_future_policy_v1.py → run_single_selected_future_policy_v1
CALL_GRAPH=
  Single Selected Future Entry Point
  → Load Productive Ranking Snapshot (Cap 2.2)
  → Validate Ranking Bindings / Digests
  → Stale + Integrity Checks
  → Selection Eligibility Classification
  → Deterministic Single Selection
  → Hysteresis + Min Holding
  → Open Position Replacement Semantics
  → Atomic Persistence
  → Selection Verification
  → Restart Reload Proof
  → Evidence
CONFIG_KEYS=selection_policy_id; selection_policy_version; selected_future_count=1; max_positions_effective=1; max_ranking_age_seconds; refresh_cadence_seconds; min_holding_period_seconds; hysteresis_rank_improvement; min_history_samples; min_data_quality_status
SELECTION_POLICY_ID=single_selected_future_policy_v1
SELECTION_POLICY_VERSION=v1
SELECTION_STATES=SELECTED_ACTIVE|SELECTED_DEGRADED|SELECTED_EXIT_ONLY|REPLACEMENT_PENDING|NO_SELECTION
PERSISTENCE=single_selected_future_selection_v1.json + single_selected_future_selection_evidence_v1.json + MANIFEST.sha256 (atomic stage/publish; single-writer lock; selection-id content idempotency)
RESTART_SEMANTICS=Produce→Persist→Restart→Load→Validate→identical selection truth; stale/corrupt/mismatched/missing → NO_SELECTION + ALPHA_BLOCKED; no runtime activation
FAILURE_SEMANTICS=missing/invalid/stale ranking, digest/SHA/config mismatch, no candidates, data-quality/history/mark/suspended failures, duplicate writer, selection-id content conflict, persistence/partial/crash, dashboard/allowlist/manual-override inputs → fail-closed
SAFETY_INVARIANTS=SELECTION_AUTHORITY_OWNER_SINGLE; DASHBOARD_AUTHORITY=false; ALLOWLIST_SELECTION_AUTHORITY=false; no alpha/execution/multi-future/runtime activation; Cap 2.2 ranking is sole productive candidate input; open position → no silent switch / no replacement alpha
CORE_LOGIC_CHANGE=false
TEST_PLAN=tests/ops/test_single_selected_future_policy_v1.py
EVIDENCE_PLAN=docs/evidence/capability_2_3_single_selected_future_policy_v1/
ACTIVATION_STATE=CODE_EXISTS_BOUND_PERSISTED_RESTART_PROVEN_NOT_ACTIVATED
ROLLBACK_PLAN=do not bind runtime callers; leave selection unused
DOCS_UPDATE=Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md; PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md
NOTION_UPDATE=false
```

## Capability closure markers

```text
CODE_EXISTS=true
BOUND=true
RUNTIME_REACHABLE=true
PERSISTED=true
RESTART_PROVEN=true
ACTIVATED=false
SINGLE_SELECTED_FUTURE=true
SELECTED_FUTURE_COUNT=1
MAX_POSITIONS_EFFECTIVE=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
SELECTION_AUTHORITY_ADDED=true
ALPHA_AUTHORITY_ADDED=false
DASHBOARD_AUTHORITY=false
CORE_LOGIC_CHANGE=false
ACTIVATION_CHANGED=false
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
```

## Open-position semantics

```text
SELECTED_ACTIVE
SELECTED_DEGRADED
SELECTED_EXIT_ONLY
REPLACEMENT_PENDING
NO_SELECTION
```

While a position is open on the selected instrument:

- no silent instrument switch
- no alpha authority for a replacement instrument
- risk / safety / exit / reconciliation remain bound to the open instrument
- replacement is persisted only as `REPLACEMENT_PENDING`

## Explicit non-claims

- Runtime binding / Cap 2.4 is owned separately (`CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1`).
- Alpha / execution / live / testnet / paper are not authorized.
- Multi-Future runtime is not authorized.
- Dashboard/UI/readmodel data is never selection authority.
- Instrument allowlists are not selection authority.
- Master V2 / Double Play / Risk / Safety / Confirmation are unchanged (`CORE_LOGIC_CHANGE=false`).
- Numeric Volatility Max-Age remains non-enforcing.
