# Canonical Fill-Conversion Ledger Long-Panel v1

```text
SLICE=CANONICAL_FILL_CONVERSION_LEDGER_LONG_PANEL_V1
BASE_SHA=bf74d4e3b15daeb6b4d25411ebd016694c54370b
BRANCH=audit/canonical-fill-conversion-ledger-long-panel-v1
PRODUCTIVE_FILES_CHANGED=false
STATUS=PASS
MECHANICAL_DEFECT_FOUND=false
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
LIVE_AUTHORIZED=false
ORDERS=false
```

## Verdict

On the full canonical 118-member futures panel (same durable offline archive as
PR #5342), Intent→Mapped-Signal→Engine-Signal conversion is **mechanically
intact** (`map`/`engine` mismatches = 0; funnel↔engine parity true). Residual
zero-trade cases (52/118 with enter intents) drop at
`backtest_engine_fill_or_roundtrip_ledger` under sparse single-bar enter impulses
(median impulse length 1). Not classified as a productive authority/binding bug.

## Panel totals

| Metric | Value |
|--------|------:|
| Instruments | 118 |
| Bars | 348454 |
| Entry intents | 4226 (long 69 / short 4157) |
| Exit/reduce | 240230 |
| Mapped nonzero bars | 4226 |
| Engine nonzero bars | 4226 |
| Total trades | 69 |
| Instruments with enter | 115 |
| Instruments with trades | 63 |
| Enter+zero-trade | 52 |
| Mechanical defects | 0 |

## Class counts

| Class | N |
|-------|--:|
| CONVERTED | 63 |
| ENGINE_SIGNAL_PRESENT_LEDGER_ZERO_TRADE | 52 |
| NO_ENTRY_INTENT | 3 |

## Separation

1. Technical chain binding — PASS (`mv2_decision_replay_series`)
2. Intent generation — present on 115/118
3. Intent→map — no drop
4. Map→engine — no drop / no exposure-gate zeroing on enter epochs
5. Engine→ledger trades — sparse conversion (69 trades / 4226 enters)
6. Mechanical defect — **false**

## Safety

Evidence-only. No productive changes. No parameter tunes. No runtime/live/orders.
PR #5342 left OPEN and untouched.
