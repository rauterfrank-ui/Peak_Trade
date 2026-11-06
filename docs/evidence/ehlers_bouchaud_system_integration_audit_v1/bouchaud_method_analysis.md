# Bouchaud Method Analysis

## What is actually implemented?

### A) Strategy (`BouchaudMicrostructureStrategy`)

**Implemented:** Deterministic **bar-level pressure proxies** producing long/flat `{0,1}`:

1. If `bid_size`+`ask_size` and `use_orderbook_imbalance`:  
   `imbalance=(bid-ask)&#47;(bid+ask)` → rolling mean → `> imbalance_threshold`
2. Else if OHLC present:  
   `pressure=(close-open)&#47;(high-low)` clipped → rolling mean → threshold
3. Else close-only:  
   `close > SMA(lookback_ticks)`

**Not implemented:** Square-root impact law, propagator convolution, trade-sign classification, metaorder splitting, L2/L3 order book dynamics. Config knobs `propagator_decay` / `use_trade_signs` / `min_liquidity_filter` are **inert**.

### B) Research feature matrix (`compute_ohlcv_proxy_features_v0`)

OHLCV-derived proxies **inspired by** impact / imbalance concepts, explicitly tagged `DETERMINISTIC_OHLCV_PROXY`, with `OHLCV_PROXY_IS_NOT_TRUE_ORDER_BOOK_MICROSTRUCTURE=True`. Includes e.g. `|ret|&#47;vol`, `|ret|&#47;volume` (Kyle-λ proxy), short/long impact ratio — **not** calibrated Bouchaud propagators.

## Data requirements vs reality

| Needed for true Bouchaud microstructure | What Peak_Trade uses |
|---|---|
| Tick trades + quotes, L2 depth | Finalized OHLCV bars (and optional bid/ask size columns if present) |
| Signed volume / Lee-Ready | Proxy from bar OHLC or missing |
| Participation / metaorder | Not in strategy path |

Assumptions are **explicitly labeled proxy** in research prep and strategy docstrings.

## Output character

| Surface | Output | Affects |
|---|---|---|
| Strategy | `{0,1}` long/flat signals | Strategy intent **if** selected in offline/backtest |
| Feature matrix | Numeric proxy features + forward return target | Offline linear diagnostics / promotion research only (`RUNTIME_EFFECT=NONE`) |
| Observability `estimated_market_impact` | `participation * 10000` | **Not Bouchaud** (false positive) |

## Authority / chain

- Offline versioned binding: `authority_effect=NONE`, baseline `INCONCLUSIVE`
- Not in Master V2 / Double Play / `transition_state`
- Agreement encoding known as `POSITIONAL_LONG01` but side agreement stays **NEUTRAL**
- No direct risk/sizing/execution kernel coupling for live paths
- Fail-closed: feature prep raises `INSUFFICIENT_DATA`; strategy raises if `close` missing; rolling uses `min_periods=1` (soft start)

## Calibration / OOS evidence

- No square-root coefficient calibration found
- Offline economic baseline: inconclusive / retry-blocked artifacts
- Feature matrix has no-lookahead contract artifacts in research prep design (`TARGET_SHIFT`, time-ordered validation policy)
- Lead-lag suite under `cross_sectional_futures_lead_lag_*` does **not** cite Bouchaud → separate research family

## Primary role

**STRATEGY_INTENT** for the registry strategy (research-gated). Research feature surface is **RESEARCH_ONLY** / liquidity-impact **proxy information**, not a cost model authority.

## Recommendation

**KEEP_RESEARCH_ONLY** — high proxy-data risk; no true microstructure law; inconclusive offline evidence; do not wire into MV2, Agreement as authority, or execution impact without a governed data upgrade (tick/L2) and non-claim repair.
