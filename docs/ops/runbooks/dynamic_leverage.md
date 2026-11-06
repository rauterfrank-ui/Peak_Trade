# Dynamic Leverage Sizing Contract (cap 50×)

## Goal
Compute a **deterministic leverage multiplier** from a normalized risk/signal strength while enforcing **hard safety caps**.

## Inputs
- `strength`: normalized in `[0, 1]` (0 = no conviction, 1 = max conviction)
- Config:
  - `min_leverage` (>= 0)
  - `max_leverage` (>= min; hard cap, e.g. 50.0)
  - `gamma` (>= 1): convexity of scaling curve

## Output
- `leverage` float satisfying:
  - `min_leverage <= leverage <= max_leverage`
  - monotonic: if `a <= b` then `L(a) <= L(b)` for `a,b in [0,1]`
  - deterministic, no randomness, no time dependence

## Fail-Closed
Invalid config or NaN inputs raise `ValueError` to prevent silent unsafe sizing.
