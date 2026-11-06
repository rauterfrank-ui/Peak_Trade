# Canonical SHORT Binding Miswiring Trace v1

Evidence-only audit following PR #5344.

## Question

Is the post-#5344 value-loss at `backtest_engine_fill_or_roundtrip_ledger` caused by a
**consumer binding / capability / adapter miswiring**, rather than a mechanical fill defect?

## Verdict (letter B)

**Contract-Capability-Mismatch:** Upstream MV2/DP +
`map_decision_evidence_to_position_signal_v1` allow SHORT (`enter_short→-1`), but the
canonical binding hard-selects `BacktestEngine(use_execution_pipeline=False)`, which is
long-open-only. A short-capable pipeline consumer exists and remains unbound. No
pre-dispatch capability gate is present, so the incompatibility surfaces as a silent
engine no-op.

Supporting letters: **C** (wrong consumer binding), **E** (adapter semantic mismatch),
**F** (missing capability gate).

## Safety

- `entry_side=NONE` fail-closed
- Runtime Bridge `BOUND_NOT_ACTIVATED`
- `LIVE_AUTHORIZED=false`, `ORDERS=false`
- No productive `src/` mutation
- No SHORT activation / repair in this slice

## Harness

`short_binding_miswiring_harness_v1.py` — scenarios S01–S19.

## Key artifacts

| File | Purpose |
|------|---------|
| `canonical_binding_matrix.json` | Producer/consumer matrix |
| `long_short_call_graph.json` | LONG vs SHORT route map |
| `consumer_capability_matrix.json` | Legacy vs pipeline capabilities |
| `first_divergence_analysis.json` | Miswiring vs value-loss boundaries |
| `blocker_classification.json` | Classification + verdict letter |
| `verdict.txt` | Compact machine-readable verdict |
