# Conclusions — Fill / Roundtrip / Ledger Boundary Trace v1

Strict separation of observation, inference, and hypothesis.

## Observation

1. Harness scenarios A–L all pass (`scenarios_pass=12`).
2. LONG Entry→Exit→Roundtrip→Ledger completes 1:1 (scenario A).
3. `enter_short` maps to `-1` and yields zero fills/roundtrips/ledger rows on the
   canonical legacy engine (scenario B); first-loss boundary =
   `backtest_engine_fill_or_roundtrip_ledger`.
4. `entry_side=NONE` yields `directional_cycle=None` and zero trades (scenario C).
5. Sizing reject increments `blocked_trades` and produces zero trades (scenario D).
6. Fill vs open and exit-fill vs roundtrip are not separable layers on the legacy path
   (scenarios E, G).
7. Unmatched signal-exit still EOD-closes under `run_realistic` (scenario F).
8. Ledger rows appear iff `materialize_trade_ledger_rows_v0` is called (scenario H).
9. Partial reduction flag is `False` (scenario I).
10. Nonzero fees/slippage with cost application preserve trade existence (scenario J).
11. Multi-instrument ledger materialization does not cross-match ids (scenario K).
12. Duplicate timestamps keep stable `run_id-trade-{index}` order (scenario L).
13. Static binding proof: legacy opens on `+1` only; exits on `-1` only if open;
    wiring still calls integrated replay; harness is NON-AUTHORITATIVE.
14. Safety flags: `LIVE_AUTHORIZED=false`, `ORDERS=false`,
    runtime bridge `BOUND_NOT_ACTIVATED`, no productive `src/` mutation in this slice.

## Inference

1. Primary blocker class remains **E** (`LOW_SAMPLE_OR_FIXTURE_INSUFFICIENCY`):
   SHORT-heavy (and sparse) intents do not materialize trades on the long-open-only
   legacy simulator, producing low/zero ledger density at the named boundary.
2. Secondary class **D** remains an annotation (exit/reduce pressure), not the first
   loss for the SHORT-mapped zero-trade path.
3. Classes A/B/C/F/G are excluded or not observed for this boundary slice.
4. The zero/low-trade path after PR #5343 is explained by **contractual engine open
   semantics + fixture/intent mix**, not by a proven mechanical fill/ledger bug.

## Hypothesis (unproven / out of scope)

1. Binding a short-capable execution pipeline as MV2 research default would raise
   SHORT roundtrip counts without changing decision authority — requires separate GO.
2. Changing map semantics (`enter_short` not mapping to `-1`) would be a second
   authority / contract break and is forbidden without explicit ratification.
3. Panel economics under class F/G remain undecided without a dedicated cost/edge panel.
