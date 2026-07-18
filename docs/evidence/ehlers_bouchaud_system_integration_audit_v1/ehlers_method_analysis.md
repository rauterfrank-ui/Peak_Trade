# Ehlers Method Analysis

## What is actually implemented?

**Implemented:** John Ehlers **Super Smoother** (recursive 2-pole / Butterworth-like coefficients) on `close`, followed by a simple rule:

- Long (`1`) if `close > super_smoother(close, period=min_cycle_length)`
- Flat (`0`) otherwise

**Not implemented (stubs / unused config):**

| Claimed in docs/config | Code reality |
|---|---|
| Hilbert Transform dominant cycle | `_measure_dominant_cycle` returns constant; **not called** |
| Bandpass cycle isolation | `_bandpass_filter` returns zeros; **not called** |
| `smoother_type` two_pole/three_pole | Comment: falls through to Super Smoother path |
| `use_hilbert_transform`, `bandpass_bandwidth`, `cycle_threshold`, `max_cycle_length` | Stored on config; **unused in `generate_signals`** |
| MAMA/FAMA, Fisher, Roofing, Decycler, Cyber Cycle, MESA | **No implementation found** |

## Formula authenticity

Super Smoother coefficients match the common Ehlers / TradingView recursion:

- `a1 = exp(-√2 · π / period)`
- `c2 = 2·a1·cos(√2 · π / period)`, `c3 = -a1²`, `c1 = 1 - c2 - c3`
- Recurrence uses `x[i]`, `x[i-1]`, `out[i-1]`, `out[i-2]` only → **causal**

Docs cite „Rocket Science for Traders“ / Cybernetic Analysis. The **signal rule** (close vs smooth) is a minimal research slice, not a full Ehlers cycle-trading system.

## I/O

| Direction | Content |
|---|---|
| Inputs | OHLCV DataFrame; requires `close`; uses lookback bars |
| Outputs | `pd.Series` int `{0,1}` (+ attrs: `is_research_stub=False`, warmup flags) |
| Measures | Noise-reduced trend relative to smoother — **not** measured cycle period/phase in the live path |
| LONG/SHORT | **Long-only** positional 0/1; **no Short** |

## Architecture roles

| Question | Answer |
|---|---|
| Dynamic Scope / Bull-Bear / Switch? | **No** — absent from `src/trading/master_v2/` |
| Master V2 / Double Play? | Contract classifies `research-only`; no MV2 binding |
| Agreement? | Encoding class `POSITIONAL_LONG01` known; intrinsic side mapping returns **NEUTRAL** for 0 and 1 (no side authority) |
| Risk/Sizing? | Offline STEP29M sizing policy exists for research eval only; not CRS/runtime authority |

## Warm-up / NaN / stability

- `len(data) < lookback` → all zeros + `insufficient_history=True` (soft, not hard fail-closed)
- Missing `close` → `ValueError`
- Super Smoother seeds `out[0]=x[0]`; deterministic for fixed input (smoke confirmed)
- Lookahead risk on implemented path: **LOW** (causal recursion). Residual **MEDIUM** only if future Hilbert/bandpass were wrongly wired with centered filters — currently unreachable stubs.

## Primary role

**STRATEGY_INTENT** (research-gated long/flat producer). Secondary marketing claims (cycle/phase) are **not** delivered by the current signal path.

## Recommendation

**KEEP_RESEARCH_ONLY** — real Super Smoother exists, but cycle stack is incomplete; offline baseline terminal inconclusive; must not enter MV2/Double Play authority without a new governed slice.
