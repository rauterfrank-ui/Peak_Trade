# Partial Fills v2 — Deterministic Bar-Based Fill Rules

## Inputs
- Bar: `MarketSnapshot( open, high, low, close, volume, ts )`
- Order: side (BUY/SELL), type (MARKET/LIMIT/STOP_MARKET), qty (base units), limit_price (optional), stop_price (optional)
- Config: fees, slippage_bps, partial_fills_v2:
  - `max_fill_ratio_per_bar` in (0,1] (default 1.0)
  - `min_fill_qty` >= 0 (default 0)
  - `volume_cap_ratio` in (0,1] (default 1.0)  # cap vs bar volume
  - `price_rule` = { "worst", "mid", "close" } (default "worst")
  - `touch_mode` = { "touch", "through" } (default "touch")  # limit/stop trigger semantics
  - `rounding` = { "none", "floor", "ceil" } (default "none") with `qty_step` (optional)
  - `allow_partial_on_trigger_bar` bool (default true)

## Determinism & Invariants
- No randomness. Same inputs => same outputs.
- Quantity conservation: `filled_qty + remaining_qty == original_qty` (within qty_step rounding).
- Fees apply only to executed qty.
- Slippage applies via deterministic price adjustment (bps) and never violates worst-case direction.

## Fill Budget per Bar
For any eligible order on a bar:
1) Remaining qty: `rem`
2) Budget by ratio: `cap_ratio = rem * max_fill_ratio_per_bar`
3) Budget by volume: `cap_vol = bar.volume * volume_cap_ratio`
4) Proposed fill: `fill0 = min(rem, cap_ratio, cap_vol)`
5) Apply min-fill: if `fill0 < min_fill_qty` => fill = 0 (no fill), else fill = fill0
6) Apply rounding (optional):
   - none: keep
   - floor/ceil to `qty_step`

## Eligibility by Order Type

### MARKET
- Always eligible on each bar until fully filled (subject to budget).
- Fill price:
  - Base price = `bar.open` (for determinism at bar start)
  - Apply `price_rule` adjustment:
    - worst: BUY uses `bar.high`, SELL uses `bar.low`
    - mid: `(bar.high + bar.low)&#47;2`
    - close: `bar.close`
  - Apply slippage bps in direction that worsens:
    - BUY: `price *= (1 + slippage_bps&#47;10_000)`
    - SELL: `price *= (1 - slippage_bps&#47;10_000)`

### LIMIT
- Eligibility depends on touch_mode:
  - BUY limit fills if bar.low <= limit_price (touch) or bar.low < limit_price (through)
  - SELL limit fills if bar.high >= limit_price (touch) or bar.high > limit_price (through)
- If eligible, fill qty subject to budget.
- Fill price (deterministic):
  - worst: BUY uses min(limit_price, bar.high) but must be <= limit_price -> so BUY uses `limit_price`
          SELL uses `limit_price`
  - mid/close: clamp to limit where needed, but final must satisfy limit constraint:
    - BUY final_price = min(candidate, limit_price)
    - SELL final_price = max(candidate, limit_price)
- Apply slippage bps but still respect limit constraint:
  - BUY: price_after_slip = min(limit_price, candidate*(1+slip))
  - SELL: price_after_slip = max(limit_price, candidate*(1-slip))

### STOP_MARKET
- Trigger condition (touch_mode):
  - BUY stop triggers if bar.high >= stop_price (touch) or > (through)
  - SELL stop triggers if bar.low <= stop_price (touch) or < (through)
- Once triggered, becomes a MARKET order starting either:
  - same bar if allow_partial_on_trigger_bar=true
  - next bar otherwise
- Trigger price is stop_price (for bookkeeping); execution uses MARKET rules after trigger.

## Accounting
For each fill:
- Notional = fill_qty * fill_price
- Fee = notional * fee_rate (or fixed + rate if supported by config)
- Return Fill record: qty, price, fee, ts, order_id, bar_ts

## Non-goals (v2)
- No queue-position simulation
- No probabilistic participation
- No multi-venue liquidity splits
