# CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1

---
docs_token: DOCS_TOKEN_CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1
STATUS: CAPABILITY_AVAILABLE
scope: Productive deterministic futures ranking producer + Top-20 candidate context persistence
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY_ADDED: false
ALPHA_AUTHORITY_ADDED: false
CORE_LOGIC_CHANGE: false
ACTIVATION_STATE: CODE_EXISTS_BOUND_PERSISTED_RESTART_PROVEN_NOT_ACTIVATED
HARD_STOP: true
---

```text
CAPABILITY_ID=CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1
TITLE=Productive Futures Ranking Producer (Capability 2.2)
OWNER_REQUIREMENT=Consume Cap 2.1 governed universe snapshot; produce deterministic Top-20 candidate-context ranking snapshot with atomic persistence and restart proof; no selection/alpha/execution
CURRENT_STATE=CODE_EXISTS+BOUND+RUNTIME_REACHABLE+PERSISTED+RESTART_PROVEN; ACTIVATED=false; SINGLE_SELECTED_FUTURE/MULTI_FUTURE/ALPHA not granted
TARGET_STATE=Ranking candidate-context authority available for later Capability 2.3 SINGLE_SELECTED_FUTURE policy without live activation
OUT_OF_SCOPE=Master V2/Double Play/Bull-Bear/Selection/Risk/Safety/Exit/Volatility Enforcement/Authorization Consumption/Session Lifecycle/Live/Testnet/Paper Activation/Rulesets/Notion/Dashboard Authority/Top-N Active Set
AUTHORITY_OWNER=ops.productive_futures_ranking_producer_v1
PRODUCTIVE_ENTRYPOINT=scripts/ops/run_productive_futures_ranking_producer_v1.py → run_productive_futures_ranking_producer_v1
CALL_GRAPH=
  Productive Ranking Entry Point
  → Load Governed Universe Snapshot (Cap 2.1)
  → Validate Universe Bindings / Digests
  → Stale + Integrity Checks
  → Structural Eligibility Classification
  → Deterministic Score + Tie-Break
  → Top-20 Candidate Context
  → Atomic Persistence
  → Snapshot Verification
  → Restart Reload Proof
  → Evidence
CONFIG_KEYS=ranking_policy_id; ranking_policy_version; top20_candidate_context_limit=20; max_universe_age_seconds; max_positions=1 (Phase-1 preserved, not selection)
RANKING_POLICY_ID=productive_futures_universe_structural_ranking_v1
RANKING_POLICY_VERSION=v1
RANKING_POLICY_PROVENANCE=Cap 2.1 instrument structural gates as equal binary score components; Cap 2.2 owner requirements for data-quality eligibility, deterministic tie-break, Top-20 context. No trading-alpha heuristic. No research/dashboard formulas.
PERSISTENCE=productive_futures_ranking_snapshot_v1.json + productive_futures_ranking_evidence_v1.json + MANIFEST.sha256 (atomic stage/publish; single-writer lock; snapshot-id content idempotency)
RESTART_SEMANTICS=Produce→Persist→Restart→Load→Validate→identical ranking truth; ALPHA_ALLOWED remains false; no SINGLE_SELECTED_FUTURE
FAILURE_SEMANTICS=missing/invalid/stale universe, digest/SHA/config mismatch, missing metadata, mark-price unsupported, no eligible candidates, duplicate writer, snapshot-id content conflict, persistence/partial/crash → fail-closed; dashboard/legacy ranker inputs rejected
SAFETY_INVARIANTS=RANKING_AUTHORITY_OWNER_SINGLE; TOP20_IS_CONTEXT_ONLY; DASHBOARD_AUTHORITY=false; no selection/alpha/execution/multi-future authority; Cap 2.1 universe is sole CURRENT productive input; future economic dual-input authorized; Economic-MD producer implemented not wired; CAP22_BECOMES_NETWORK_OWNER=false; CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false; ECONOMIC_MD_PRODUCER_IMPLEMENTED=true; ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false; FINAL_SCORE_FORMULA_RATIFIED=false
CORE_LOGIC_CHANGE=false
TEST_PLAN=tests/ops/test_productive_futures_ranking_producer_v1.py
EVIDENCE_PLAN=docs/evidence/capability_2_2_productive_futures_ranking_producer_v1/
ACTIVATION_STATE=CODE_EXISTS_BOUND_PERSISTED_RESTART_PROVEN_NOT_ACTIVATED
ROLLBACK_PLAN=do not bind selection callers; leave producer unused
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
PRODUCTIVE_RANKING_PRODUCER_IMPLEMENTED=true
TOP20_CANDIDATE_CONTEXT_AVAILABLE=true
SINGLE_SELECTED_FUTURE_AUTHORITY=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
CAP22_INPUT_MODEL=DUAL_AUTHORITATIVE_INPUTS_WITH_SEPARATE_ROLES
CAP22_BECOMES_NETWORK_OWNER=false
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false
ECONOMIC_MD_PRODUCER_IMPLEMENTED=true
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false
FINAL_SCORE_FORMULA_RATIFIED=false
```

## Forensic classification of prior ranking surfaces

| Surface | Class |
|---|---|
| `ops.governed_futures_universe_producer_v1` | `PRODUCTIVE_REUSABLE` (input only) |
| `research&#47;cross_sectional_*` ranking bindings | `RESEARCH_ONLY` |
| `webui` universe_selection / landscape ranking | `DASHBOARD_CONSUMER_ONLY` |
| `analytics.portfolio_builder.select_top_*` | `LEGACY_DEAUTHORIZED` |
| `master_v2.FuturesRankingSnapshot` | `ORPHANED_REUSABLE_IMPLEMENTATION` (DTO shape only) |
| `suitability_ranking_policy_v1` | `INSUFFICIENT_EVIDENCE` for universe ranking |

## Explicit non-claims

- `SINGLE_SELECTED_FUTURE` is not productively closed (Capability 2.3).
- Top-20 is candidate context only — not positions, not multi-future authorization.
- Multi-Future runtime is not authorized or closed.
- Canonical runtime activation remains unchanged / fail-closed.
- Dashboard/UI/readmodel data is never ranking authority.
- Research cross-sectional formulas are not productive ranking authority.

## Future economic ranking dual-input architecture (authorized, not wired)

Owner-GO
`PEAK_TRADE_CAP_2_2_SEPARATE_ECONOMIC_MD_INPUT_CAPABILITY_AND_DUAL_INPUT_CONTRACT_SPEC_ONLY_V1`
authorizes a future dual-input model. Subordinate contract:
`docs&#47;ops&#47;specs&#47;CAP22_ECONOMIC_MD_INPUT_AND_DUAL_INPUT_CONTRACT_V1.md`.

Current productive ranking remains Cap-2.1-only structural ranking.
This section does **not** rewire that producer.

```text
CAP22_ECONOMIC_MD_ARCHITECTURE_DECISION=AUTHORIZE_SEPARATE_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_CAPABILITY
CAP22_INPUT_MODEL=DUAL_AUTHORITATIVE_INPUTS_WITH_SEPARATE_ROLES
CAP22_INPUT_1=CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT
CAP22_INPUT_1_ROLE=STRUCTURAL_AND_SAFETY_ELIGIBILITY_ONLY
CAP22_INPUT_2=PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MARKET_INPUT_SNAPSHOT
CAP22_INPUT_2_ROLE=ECONOMIC_RANKING_FEATURE_INPUT_ONLY
CAP22_REMAINS_RANKING_OWNER=true
CAP22_BECOMES_NETWORK_OWNER=false
CAP22_DIRECT_LIVE_VENUE_DEPENDENCY=false
CAP22_CURRENT_PRODUCTIVE_INPUT=CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT_ONLY
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false
ECONOMIC_MD_INPUT_CAPABILITY_AUTHORIZED=true
ECONOMIC_MD_PRODUCER_IMPLEMENTED=true
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false
ECONOMIC_RANK_ACTIVATED=false
FINAL_SCORE_FORMULA_RATIFIED=false
FINAL_WEIGHTS_RATIFIED=false
LIBRARY_REUSE_AUTHORITY_TRANSFER=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

Cap 2.2 remains ranking owner and must not become network or venue SSOT.
The separate Economic-MD-Input producer owns network I/O, collection,
persistence, schema, and replay input. That producer is implemented, not
productively scheduled, and is not wired into Cap 2.2 ranking.

## Offline policy candidates and evidence contract (docs-only; not wired)

Owner-GO
`PEAK_TRADE_CAP_2_2_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_DOCS_ONLY_V1`
persists the offline challenger set and the evidence contract required
before any economic ranking policy may be ratified. Subordinate
contract:
`docs&#47;ops&#47;specs&#47;CAP22_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_V1.md`.

```text
CURRENT_PRODUCTIVE_ECONOMIC_RANKING=NONE
CURRENT_PRODUCTIVE_RANKING_POLICY=productive_futures_universe_structural_ranking_v1
CURRENT_STRUCTURAL_RANKING_IS_ECONOMIC_POLICY=false
RECOMMENDED_PRIMARY_BASELINE=VOLATILITY_RANK_ONLY
VOLATILITY_RANK_ONLY_VERDICT=BASELINE_ONLY
NEGATIVE_STATUS_QUO_BASELINE=CURRENT_STRUCTURAL_THEN_VENUE_ID_ASC
RECOMMENDED_OFFLINE_CHALLENGERS=HARD_SPREAD_GATE_THEN_VOLATILITY_RANK;VOLATILITY_TO_SPREAD_RATIO;LEXICOGRAPHIC_SPREAD_THEN_VOL
NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY=true
FINAL_SCORE_FORMULA_RATIFIED=false
FINAL_WEIGHTS_RATIFIED=false
ECONOMIC_RANK_ACTIVATED=false
ECONOMIC_MD_PRODUCER_IMPLEMENTED=true
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false
```

This section does **not** rewire the productive structural ranking
producer and does **not** ratify a score formula.
