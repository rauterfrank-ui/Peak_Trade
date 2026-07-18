# Canonical SHORT Binding Post-Repair Reevaluation v1

Evidence-only reevaluation after PR #5346 squash-merge.

## Question

Does the repaired MV2 research wiring transport LONG, SHORT, and NONE
end-to-end through the exact prior canonical offline fixture panel?

## Verdict: `PASS_CHAIN_ONLY`

- Technical chain bound with `use_execution_pipeline=True` and
  `honor_mapped_short_entry=True`.
- Fixture panel trade_count_total=14
  (long=1, short=13).
- Focused direction probe proves SHORT fill/position/exit/ledger and
  LONG regression; NONE remains fail-closed.
- Zero-trade miswiring state is resolved.
- Economic offline gate remains **closed** (low sample / negative panel PnL).
- Master V2 / Double Play remain sole direction authority.

## Unchanged bindings

| Field | Value |
|---|---|
| CONFIG_ID | `bollinger_bands_v2_full_canonical_system_economic_binding_v1` |
| DATASET_ID | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` |
| PERIOD | `2024-05-01T00:00:00Z..2024-09-01T00:00:00Z` |
| SEED | `42` |
| STRATEGY | `bollinger_bands` / `v2` |
| FEE_BPS | `10.0` |
| SLIPPAGE_BPS | `5.0` |
| STOP_PCT | `0.025` |

## Artifacts

| File | Purpose |
|---|---|
| `post_repair_reevaluation_probe_v1.py` | Non-authoritative harness |
| `probe_summary.json` | Full machine summary |
| `direction_probe.json` | Forced LONG/SHORT/NONE proof |
| `direction_traces.json` | Stage traces per direction |
| `economics.json` | Panel economics |
| `instrument_metrics.json` | Per-instrument rows |
| `claims.json` / `verdict.txt` | Machine claims |
| `result_classification.json` | RESULT_CLASS rationale |
| `manifest.json` | SHA256 inventory |

## Safety

`LIVE_AUTHORIZED=false`, `ORDERS=false`, Runtime Bridge
`BOUND_NOT_ACTIVATED`, `PRODUCTIVE_FILES_CHANGED=false`,
`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false`, `PROMOTION_ELIGIBLE=0`.

