# Market Dashboard Projection Octet Materialization-Path Discovery V1

**STATUS:** `READ_ONLY_DISCOVERY_COMPLETE`  
**GENERATED_AT:** `2026-08-04T19:54:24Z`  
**HEAD / ORIGIN_MAIN:** `8aa5606fc08419d5e436a1e4db414deb680e9f71`  
**PRIOR BATCH:** B2 Projection Octet Runtime Verify (`ARTIFACTS_PRESENT=0`, `MATERIALIZER_EXECUTED=false`)

## Verdict

Recommendation **D — MIXED_BLOCKERS_REQUIRE_BOUNDED_FAMILY_PLAN**.

All eight presentation materializers exist as library entrypoints and are proven only in isolated tests. No operational/manual/automatic invocation path exists. The active archive also lacks the durable source siblings (and all eight presentation projections). Safety Authority has no durable sibling loader at all.

This discovery does **not** authorize materialization, B3, runtime/producer changes, or dashboard mutation.

## Authority chain (unchanged)

```text
Trading SSOT
→ authorized Read Models / Evidence / durable source siblings
→ authorized durable Presentation Projections
→ Dashboard PURE_CONSUMER
```

Dashboard role remains `PURE_CONSUMER` / `AUTHORITY_EFFECT=NONE`. Loaders call `try_load_*` only; they never call materializers.

## Active archive observation (read-only)

Archive root (from B2 VERIFY):

`/Users/frnkhrz/Library/Application Support/Peak_Trade/workflow_dashboard_v1_okx_fresh_20260724T214822Z`

Present under `readmodels&#47;`:

- `okx_selected_instrument_ohlcv_readmodel.v1.json`
- `universe_selection_readmodel.v1.json`
- manifest files

Absent: all seven defined source siblings and all eight presentation projections.

## Family matrix (summary)

| family_id | materializer_symbol | source_sibling | source present | output | schema_id | invocation_mode |
|---|---|---|---|---|---|---|
| dynamic_scope | `materialize_dynamic_scope_presentation_projection_v1` | `readmodels&#47;dynamic_scope_state_v1.json` | NO | `readmodels&#47;dynamic_scope_presentation_projection.v1.json` | `dynamic_scope_presentation_projection.v1` | TEST_ONLY_PATH |
| regime_bull_bear_switch | `materialize_bull_bear_regime_presentation_projection_v1` | `readmodels&#47;regime_bull_bear_switch.v1.json` | NO | `readmodels&#47;bull_bear_regime_presentation_projection.v1.json` | `bull_bear_regime_presentation_projection.v1` | TEST_ONLY_PATH |
| canonical_decision | `materialize_canonical_decision_presentation_projection_v1` | `readmodels&#47;canonical_trading_decision_evidence.v1.json` | NO | `readmodels&#47;canonical_decision_presentation_projection.v1.json` | `canonical_decision_presentation_projection.v1` | TEST_ONLY_PATH |
| double_play | `materialize_double_play_presentation_projection_v1` | `readmodels&#47;double_play_dashboard_display.v1.json` | NO | `readmodels&#47;double_play_presentation_projection.v1.json` | `double_play_presentation_projection.v1` | TEST_ONLY_PATH |
| safety_authority | `materialize_safety_authority_presentation_projection_v1` | *none (caller object required)* | N/A | `readmodels&#47;safety_authority.v1.json` | `safety_authority_presentation_projection.v1` | TEST_ONLY_PATH |
| risk_sizing_capital | `materialize_risk_sizing_capital_presentation_projection_v1` | `readmodels&#47;risk_sizing_capital.v1.json` | NO | `readmodels&#47;risk_sizing_capital_presentation_projection.v1.json` | `risk_sizing_capital_presentation_projection.v1` | TEST_ONLY_PATH |
| execution_reconciliation | `materialize_execution_reconciliation_presentation_projection_v1` | `readmodels&#47;execution_reconciliation.v1.json` | NO | `readmodels&#47;execution_reconciliation_presentation_projection.v1.json` | `execution_reconciliation_presentation_projection.v1` | TEST_ONLY_PATH |
| economic_summary | `materialize_economic_summary_presentation_projection_v1` | `readmodels&#47;economic_summary.v1.json` | NO | `readmodels&#47;economic_summary_presentation_projection.v1.json` | `economic_summary_presentation_projection.v1` | TEST_ONLY_PATH |

Full machine-readable rows: `FAMILY_MATRIX.json`.

## Invocation findings

- AST scan over `src/`, `scripts/`, `tests/`: **0 non-test call sites** for all eight `materialize_*_presentation_projection_v1` symbols; test call sites only.
- No `__main__` / argparse CLI in materializer modules.
- No matching ops scripts under `scripts/` or `config/`.
- No LaunchAgent / supervisor contract referencing these materializers found in-repo.
- No O-series / session-start / closeout path proven to invoke them.
- Dashboard binder (`market_dashboard_landscape_producer_binding_v2.py`) imports loaders only.
- Even when a durable sibling is present, materializers still require a caller-supplied `generated_at` (fail-closed otherwise).

## Octet classification

- Structural: **EIGHT_INDEPENDENT_PATHS_PROVEN** (eight modules/symbols; shared archive-root convention; no common orchestrator).
- Operational: **NO_OPERATIONAL_PATH_PROVEN**.

## Semantic mutation assessment

Existing materializer designs write only non-authoritative presentation projection JSON (`AUTHORITY_EFFECT=NONE`). Repository evidence does not show any existing path that would mutate trading logic, producers, runtime processes, or canonical authority-chain read models. Authorized future writes would still mutate archive presentation artifacts only — and remain unauthorized without separate Owner-GO.

## B3

`B3_AUTHORIZED=false`. Active Double Play projection remains absent; blocker-field contract is not proven on a real artifact.

## Owner decision input

See `OWNER_DECISION_INPUT.json`.

**Recommendation:** `D. MIXED_BLOCKERS_REQUIRE_BOUNDED_FAMILY_PLAN`

Next owner decision required: bounded family plan / stop. No materialization authorized by this discovery.
