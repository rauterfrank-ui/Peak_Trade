# Canonical Data-Flow Map — Fill / Roundtrip / Ledger Boundary Trace v1

Slice: `CANONICAL_FILL_ROUNDTRIP_LEDGER_BOUNDARY_TRACE_V1`  
Base: `f5f5fee56e471621988b5d193397d0b7b80eb535`  
Role: diagnose conversion of canonical decisions into fills, roundtrips, and ledger rows.

```text
Strategy signal
  → Canonical market context
  → Master V2 / Double-Play state + composition
  → Canonical decision / order intent
  → Backtest-engine invocation
  → Fill creation (legacy: Trade open)
  → Position / open-state mutation
  → Exit matching
  → Roundtrip creation (completed Trade)
  → Trade-ledger persistence
  → Metrics / report consumer
```

---

## 1. Strategy signal

| Field | Value |
|-------|-------|
| Owner | `execute_configured_strategy_signal_series_v1` |
| Module | `src/backtest/strategy_signal_binding_v1.py` |
| Input | bars DataFrame, `strategy_id`, cfg |
| Output | `StrategySignalBindingResultV1` (signal Series + digests) |
| Side semantics | Raw producer encoding (`+1&#47;0&#47;-1`); **not** side authority |
| Quantity/price | N/A at this stage |
| Identifiers | strategy digests / instrument binding |
| Timestamp | bar index |
| Fail-closed | empty bars, unknown/stub strategy, digest mismatch |
| Drop/filter | producer flat / no-event bars |
| Call sites | `run_mv2_research_backtest_wiring_v1` |
| Tests | `tests/backtest/test_engine_signal_source_mv2_replay_binding_contract_v0.py` |
| Authority? | **Consumer/Adapter** (Bollinger event authority is separate contract) |

## 2. Canonical market context

| Field | Value |
|-------|-------|
| Owner | `bind_canonical_market_context_event` / bar→CMC binders |
| Module | `src/trading/master_v2/canonical_market_context_v1.py`; wiring in `mv2_research_wiring_v1.py` |
| Input | historical bar / L1-modelled observation |
| Output | `CanonicalMarketContextV1` (`instrument_id`, `trading_epoch`, `mark_price`, trust/finality) |
| Side | none |
| Fail-closed | unfinalized / untrusted CMC in replay |
| Call sites | `run_integrated_offline_trading_logic_replay_v1` |
| Authority? | **Authority** for market-context eligibility; wiring is adapter |

## 3. Master V2 / Double-Play state and composition

| Field | Value |
|-------|-------|
| Owners | `transition_state` (`double_play_state.py`); `evaluate_double_play_composition_matrix_v1`; `evaluate_double_play_entry_exit_policy_v0` |
| Orchestrator | `run_integrated_offline_trading_logic_replay_v1` |
| Input | CMC, scope, DA, suitability agreement material |
| Output | `decision_outcome` ∈ `{enter_long, enter_short, reduce, exit, observe, blocked, …}`, digests, `decision_id` |
| Side | **Sole** side authority = Double-Play `transition_state` + composition |
| Fail-closed | blocked / observe when gates fail |
| Authority? | **Authority** |

## 4. Canonical decision / order intent

| Field | Value |
|-------|-------|
| Owner | evidence build in integrated replay; offline OI bind adapter |
| Modules | `canonical_trading_decision_evidence_v1.py`; `canonical_order_intent_v1.py` |
| Output | `CanonicalTradingDecisionEvidenceV1` + offline plan-only order intent |
| Side/qty | from entry/exit + CRS sizing; offline |
| Exposure gates (wiring) | killswitch / reconciliation / CRS / COI / safety may zero engine signal |
| Authority? | Decision/OI offline = **Authority**; gates = consumer adapters |

## 5. Backtest-engine invocation

| Field | Value |
|-------|-------|
| Owner | `BacktestEngine.run_realistic` (`use_execution_pipeline=False` default MV2 research) |
| Module | `src/backtest/engine.py`; invoked from `mv2_research_wiring_v1.py` |
| Signal source | `engine_signal_series` from `map_decision_evidence_to_position_signal_v1` |
| Map | `enter_long→+1`, `enter_short→-1`, else `0` |
| Alt path | `step_legacy_realistic_bar_v1` + `finalize_legacy_realistic_bar_loop_v1` |
| Authority? | **Fill simulator / Consumer** — not decision owner |

## 6. Fill creation

| Field | Value |
|-------|-------|
| Canonical MV2 legacy | **No separate Fill object** |
| Mechanism | `Trade(...)` open when `signal == 1` and flat |
| Price | bar `close`; stop = `entry * (1 - stop_pct)` |
| Quantity | position sizer / offline sizing / core sizer |
| Side | accounting hardcoded `"long"` on emit |
| Drop | sizing reject, min notional, max position %, risk → `blocked_trades++` |
| Tests | `tests/backtest/test_engine_legacy_gross_pnl_trade_record_emission_v0.py`, position-feedback tests |
| Authority? | **Consumer / simulator** |

## 7. Position / open-state mutation

| Field | Value |
|-------|-------|
| Owner | `current_trade: Optional[Trade]` in legacy loop |
| Feedback | `capture_backtest_engine_position_feedback_v1` — observation only; `side_state` remains NEUTRAL |
| Flag | `BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE = False` |
| Authority? | **Consumer** (must not write Double-Play side) |

## 8. Exit matching

| Trigger | Condition |
|---------|-----------|
| Stop | `bar.low <= stop_price` |
| Signal exit | `signal == -1` **and** open trade |
| EOD | open trade at end of data |

Critical: `signal == -1` without open long = **no-op** (no short open on legacy path).

## 9. Roundtrip creation

Completed `Trade` with entry+exit+PnL:

1. Exit sets `exit_time&#47;price&#47;pnl&#47;exit_reason`
2. `_emit_legacy_trade_accounting_fields_v0` (`side="long"`)
3. Append to `trades`; equity update
4. `BacktestResult.trades` + `stats.total_trades`

Default `LEGACY_PATH_COST_APPLICATION=False` → costs 0; existence unchanged.

## 10. Trade-ledger persistence

| Field | Value |
|-------|-------|
| Owner | `TRADE_LEDGER_OWNER = "backtest.trade_ledger_equity_curve_persistence_v0"` |
| Functions | `materialize_trade_ledger_row_v0` / `_rows_v0`; `serialize_trade_ledger_jsonl` |
| Side | `_side_from_size` (size>0→long); legacy size always positive → long |
| IDs | `trade_id = {run_id}-trade-{i}` if absent |
| Fail-closed | reconciliation raise; missing fields → `SOURCE_MISSING` (no zero-fill) |
| Authority? | **Consumer / materializer** |

## 11. Metrics / report consumer

| Field | Value |
|-------|-------|
| Owner | `render_canonical_economic_report_v1` |
| Modules | `economic_observability_report_consumer_v1.py`, derived metrics |
| Authority? | **Pure Consumer** |

---

## Boundary name semantics

`backtest_engine_fill_or_roundtrip_ledger` = engine-facing nonzero mapped/engine signal present, but completed trade / ledger rows remain zero.

Dominant productive mechanism on the canonical legacy path:

- `enter_short` → mapped `-1` → **no open** when flat → zero roundtrip
- Sparse `enter_long` may still EOD-close; panel residual also includes sizing blocks and exit-heavy reduce pressure (class D annotation)
