# CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1

---
docs_token: DOCS_TOKEN_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1
STATUS: CAPABILITY_AVAILABLE
scope: Productive governed OKX-EEA futures-only universe snapshot producer + atomic persistence
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
RANKING_AUTHORITY_ADDED: false
SELECTION_AUTHORITY_ADDED: false
ALPHA_AUTHORITY_ADDED: false
CORE_LOGIC_CHANGE: false
ACTIVATION_STATE: CODE_EXISTS_BOUND_PERSISTED_RESTART_PROVEN_NOT_ACTIVATED
HARD_STOP: true
---

```text
CAPABILITY_ID=CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1
TITLE=Governed Futures Universe Producer (Capability 2.1)
OWNER_REQUIREMENT=Produce canonical, versioned, persistable OKX-EEA futures-only universe truth with fail-closed eligibility and restart-proven snapshot load
CURRENT_STATE=CODE_EXISTS+BOUND+RUNTIME_REACHABLE+PERSISTED+RESTART_PROVEN; ACTIVATED=false; RANKING/SELECTION/ALPHA not granted
TARGET_STATE=Universe authority available for later Phase-1 Ranking → SINGLE_SELECTED_FUTURE binding without live activation
OUT_OF_SCOPE=Master V2/Double Play/Bull-Bear/Ranking/Selection/Risk/Safety/Exit/Volatility Enforcement/Authorization Consumption/Session Lifecycle/Live/Testnet/Paper Activation/Rulesets/Notion/Dashboard Authority
AUTHORITY_OWNER=ops.governed_futures_universe_producer_v1
PRODUCTIVE_ENTRYPOINT=scripts/ops/run_governed_futures_universe_producer_v1.py → run_governed_futures_universe_producer_v1
CALL_GRAPH=
  Productive Universe Entry Point
  → OKX EEA Instrument Discovery
  → Raw Metadata Validation
  → Futures-only Filter
  → BTC Exclusion
  → Canonical Instrument Normalization
  → Eligibility/Data-Quality Classification
  → Deterministic Universe Snapshot
  → Atomic Persistence
  → Snapshot Verification
  → Evidence
CONFIG_KEYS=venue=okx_eea; futures_only; btc_excluded; spot_excluded; max_source_age_seconds; max_positions=1 (Phase-1 preserved, not selection)
PERSISTENCE=governed_futures_universe_snapshot_v1.json + governed_futures_universe_evidence_v1.json + MANIFEST.sha256 (atomic stage/publish; single-writer lock)
RESTART_SEMANTICS=Produce→Persist→Restart→Load→Validate→identical canonical universe truth; ALPHA_ALLOWED remains false
FAILURE_SEMANTICS=source unavailable/malformed/missing-invalid metadata/spot/BTC/stale/duplicates/conflicts/empty universe/persistence/schema/SHA/config/writer → fail-closed; no selection/alpha
SAFETY_INVARIANTS=UNIVERSE_AUTHORITY_OWNER_SINGLE; DASHBOARD_AUTHORITY=false; no ranking/selection/alpha/execution authority; OKX EEA only; futures-only; BTC excluded; missing metadata never defaulted
CORE_LOGIC_CHANGE=false
TEST_PLAN=tests/ops/test_governed_futures_universe_producer_v1.py
EVIDENCE_PLAN=docs/evidence/capability_2_1_governed_futures_universe_producer_v1/
ACTIVATION_STATE=CODE_EXISTS_BOUND_PERSISTED_RESTART_PROVEN_NOT_ACTIVATED
ROLLBACK_PLAN=do not bind ranking/selection callers; leave producer unused
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
```

## Explicit non-claims

- Ranking is not productively closed.
- `SINGLE_SELECTED_FUTURE` is not productively closed.
- Multi-Future runtime is not authorized or closed.
- Canonical runtime activation remains unchanged / fail-closed.
- Dashboard/UI/readmodel data is never universe authority.
