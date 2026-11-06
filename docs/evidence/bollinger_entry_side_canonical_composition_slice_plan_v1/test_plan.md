# Test Plan

## Required before any productive composition slice (future)

1. Bollinger EVENT_ONLY still forces `entry_side=NONE` unless GO changes it.
2. Composer projection tests (if OPTION_B later authorized):
   - LONG only on Intent∧Bull&#47;Long
   - SHORT only on Intent∧Bear&#47;Short
   - conflict &#47; CHOP &#47; missing &#47; neutral → NONE
   - symmetry Long&#47;Short fail-closed
3. No Classic `run_realistic` authority leakage into Integrated&#47;MV2.
4. Double-Play sole-authority quarantine remains green.
5. Composition matrix conflict → NONE unchanged.
6. Order-intent builder still gated; LIVE&#47;Orders false.
7. Parity: Integrated replay and any agreement-bound backtest path share composition semantics.

## Current prep PR

No new tests. Existing non-mutating smoke already green post-audit-merge.
