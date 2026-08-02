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
SAFETY_INVARIANTS=RANKING_AUTHORITY_OWNER_SINGLE; TOP20_IS_CONTEXT_ONLY; DASHBOARD_AUTHORITY=false; no selection/alpha/execution/multi-future authority; Cap 2.1 universe is sole productive input
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
```

## Forensic classification of prior ranking surfaces

| Surface | Class |
|---|---|
| `ops.governed_futures_universe_producer_v1` | `PRODUCTIVE_REUSABLE` (input only) |
| `research/cross_sectional_*` ranking bindings | `RESEARCH_ONLY` |
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
